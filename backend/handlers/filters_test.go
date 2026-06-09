package handlers

import (
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func parseQuery(t *testing.T, q string) FilterParams {
	t.Helper()
	gin.SetMode(gin.TestMode)
	c, _ := gin.CreateTestContext(httptest.NewRecorder())
	c.Request = httptest.NewRequest("GET", "/?"+q, nil)
	return ParseFilterParams(c)
}

func TestFilterParams_ParseThemes(t *testing.T) {
	fp := parseQuery(t, "theme=AMOR,NAVIDAD")
	assert.Equal(t, []string{"AMOR", "NAVIDAD"}, fp.Themes)
}

func TestFilterParams_ParseYearRange(t *testing.T) {
	fp := parseQuery(t, "year_from=1990&year_to=2010")
	assert.NotNil(t, fp.YearFrom)
	assert.Equal(t, 1990, *fp.YearFrom)
	assert.NotNil(t, fp.YearTo)
	assert.Equal(t, 2010, *fp.YearTo)
}

func TestFilterParams_DropsInvalidIntegers(t *testing.T) {
	fp := parseQuery(t, "year_from=notanumber&year_to=2010")
	assert.Nil(t, fp.YearFrom)
	assert.NotNil(t, fp.YearTo)
}

func TestFilterParams_EmptyValues(t *testing.T) {
	fp := parseQuery(t, "")
	assert.False(t, fp.HasAny())
}

func TestFilterParams_NoneSentinelTheme(t *testing.T) {
	fp := parseQuery(t, "theme=__none__")
	assert.Equal(t, []string{"__none__"}, fp.Themes)
}

func TestFilterParams_ValidateYearRange(t *testing.T) {
	fp := FilterParams{}
	assert.Equal(t, "", fp.ValidateYearRange())

	lo, hi := 2010, 1990
	fp = FilterParams{YearFrom: &lo, YearTo: &hi}
	assert.NotEmpty(t, fp.ValidateYearRange())

	lo, hi = 1990, 2010
	fp = FilterParams{YearFrom: &lo, YearTo: &hi}
	assert.Equal(t, "", fp.ValidateYearRange())
}

func TestFilterParams_ValidateQueryLength(t *testing.T) {
	fp := FilterParams{}
	assert.Equal(t, "", fp.ValidateQueryLength(10))
	fp = FilterParams{Q: "this is way more than ten characters"}
	assert.NotEmpty(t, fp.ValidateQueryLength(10))
}

func TestApplySongFilters_NoFiltersReturnsEmpty(t *testing.T) {
	fp := FilterParams{}
	cond, args := fp.ApplySongFilters("")
	assert.Equal(t, "", cond)
	assert.Empty(t, args)
}

func TestApplySongFilters_ThemeWithNone(t *testing.T) {
	fp := FilterParams{Themes: []string{"__none__", "AMOR"}}
	cond, args := fp.ApplySongFilters("")
	assert.Contains(t, cond, "s.tema IN")
	assert.Contains(t, cond, "COALESCE(s.tema, '') = ''")
	assert.Equal(t, []interface{}{"AMOR"}, args)
}

func TestApplySongFilters_YearRange(t *testing.T) {
	lo, hi := 1990, 2010
	fp := FilterParams{YearFrom: &lo, YearTo: &hi}
	cond, args := fp.ApplySongFilters("")
	assert.Contains(t, cond, "CAST(f.anio AS INTEGER) >=")
	assert.Contains(t, cond, "CAST(f.anio AS INTEGER) <=")
	assert.Equal(t, []interface{}{1990, 2010}, args)
}

func TestApplySongFilters_AlbumAndQ(t *testing.T) {
	fp := FilterParams{Album: "Foo", Q: "bar"}
	cond, args := fp.ApplySongFilters("")
	assert.Contains(t, cond, "f.titulo = ?")
	assert.Contains(t, cond, "OR")
	assert.Equal(t, []interface{}{"Foo", "%bar%", "%bar%", "%bar%"}, args)
}

func TestApplySongFilters_PreservesPriorWhere(t *testing.T) {
	fp := FilterParams{}
	cond, args := fp.ApplySongFilters("f.anio IS NOT NULL")
	assert.Contains(t, cond, "f.anio IS NOT NULL")
	assert.Empty(t, args, "no filter params and parameterless prior where → no args")
}
