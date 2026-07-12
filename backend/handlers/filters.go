package handlers

import (
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

// FilterParams is the parsed set of dashboard filters shared by /api/stats,
// /api/search, and /api/timeline. Empty slices / nil numbers mean "no filter".
type FilterParams struct {
	Themes          []string
	YearFrom        *int
	YearTo          *int
	Clasificaciones []string
	Album           string
	Q               string
}

// HasAny reports whether at least one filter is active. Used by callers to
// decide whether to apply the WHERE clause and to short-circuit "no filters
// active" code paths.
func (f FilterParams) HasAny() bool {
	return len(f.Themes) > 0 ||
		f.YearFrom != nil ||
		f.YearTo != nil ||
		len(f.Clasificaciones) > 0 ||
		f.Album != "" ||
		f.Q != ""
}

// ParseFilterParams extracts the shared filter parameters from a Gin context.
// All parameters are optional; invalid integers silently become nil so a
// bookmarked URL with a stale value degrades gracefully.
func ParseFilterParams(c *gin.Context) FilterParams {
	return FilterParams{
		Themes:          parseList(c.Query("theme")),
		YearFrom:        parseIntPtr(c.Query("year_from")),
		YearTo:          parseIntPtr(c.Query("year_to")),
		Clasificaciones: parseList(c.Query("clasificacion")),
		Album:           strings.TrimSpace(c.Query("album")),
		Q:               strings.TrimSpace(c.Query("q")),
	}
}

func parseList(v string) []string {
	if v == "" {
		return nil
	}
	parts := strings.Split(v, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

func parseIntPtr(v string) *int {
	if v == "" {
		return nil
	}
	n, err := strconv.Atoi(strings.TrimSpace(v))
	if err != nil {
		return nil
	}
	return &n
}

// ValidateYearRange enforces year_from <= year_to and returns a user-friendly
// error string when the constraint is violated. Empty inputs are always valid.
func (f FilterParams) ValidateYearRange() string {
	if f.YearFrom == nil || f.YearTo == nil {
		return ""
	}
	if *f.YearFrom > *f.YearTo {
		return "year_from must be <= year_to"
	}
	return ""
}

// ValidateQueryLength enforces the Q max length.
func (f FilterParams) ValidateQueryLength(max int) string {
	if len(f.Q) > max {
		return "q must be at most 256 characters"
	}
	return ""
}

// ApplySongFilters appends WHERE clauses (and matching args) to an in-flight
// query that already JOINs songs (s) and fonogramas (f). The returned clauses
// start with AND because the caller is expected to have added a leading
// condition or to use the empty leading clause produced when no prior
// condition exists.
//
// The function does not validate; callers should call ValidateYearRange and
// ValidateQueryLength first.
func (f FilterParams) ApplySongFilters(priorWhere string) (where string, args []interface{}) {
	var conds []string
	if priorWhere != "" {
		conds = append(conds, priorWhere)
	}

	if len(f.Themes) > 0 {
		placeholders := make([]string, 0, len(f.Themes))
		for _, t := range f.Themes {
			if t == "__none__" {
				// Songs with null/blank tema
				conds = append(conds, "(COALESCE(s.tema, '') = '')")
				continue
			}
			placeholders = append(placeholders, "?")
			args = append(args, t)
		}
		if len(placeholders) > 0 {
			conds = append(conds, "s.tema IN ("+strings.Join(placeholders, ",")+")")
		}
	}

	if f.YearFrom != nil {
		conds = append(conds, "CAST(f.anio AS INTEGER) >= ?")
		args = append(args, *f.YearFrom)
	}
	if f.YearTo != nil {
		conds = append(conds, "CAST(f.anio AS INTEGER) <= ?")
		args = append(args, *f.YearTo)
	}

	if len(f.Clasificaciones) > 0 {
		placeholders := make([]string, 0, len(f.Clasificaciones))
		for _, c := range f.Clasificaciones {
			placeholders = append(placeholders, "?")
			args = append(args, c)
		}
		conds = append(conds, "s.clasificacion IN ("+strings.Join(placeholders, ",")+")")
	}

	if f.Album != "" {
		conds = append(conds, "f.titulo = ?")
		args = append(args, f.Album)
	}

	if f.Q != "" {
		like := "%" + f.Q + "%"
		conds = append(conds, "(s.title LIKE ? OR s.lyrics LIKE ? OR f.titulo LIKE ?)")
		args = append(args, like, like, like)
	}

	if len(conds) == 0 {
		return "", args
	}
	return strings.Join(conds, " AND "), args
}
