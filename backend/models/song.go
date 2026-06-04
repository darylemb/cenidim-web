package models

type Fonograma struct {
	ClaveFonograma         int    `json:"clave_fonograma"`
	Titulo                 string `json:"titulo"`
	Subtitulo              string `json:"subtitulo,omitempty"`
	InterpretePrincipal    string `json:"interprete_principal,omitempty"`
	InterpretesInvitados   string `json:"interpretes_invitados,omitempty"`
	InterpreteParticipante string `json:"interprete_participante,omitempty"`
	SoporteFisico          string `json:"soporte_fisico,omitempty"`
	Editora                string `json:"editora,omitempty"`
	NumeroCatalogo         string `json:"numero_catalogo,omitempty"`
	CiudadEdicion          string `json:"ciudad_edicion,omitempty"`
	PaisEdicion            string `json:"pais_edicion,omitempty"`
	Anio                   string `json:"anio,omitempty"`
	Pistas                 string `json:"pistas,omitempty"`
	Observaciones          string `json:"observaciones,omitempty"`
	Version                int    `json:"version"`
}

type Song struct {
	ID          int    `json:"id"`
	FonogramaID int    `json:"fonograma_id"`
	Title       string `json:"title"`
	Filename    string `json:"filename"`
	Version     int    `json:"version"`

	// All fonograma columns (joined)
	Album                  string `json:"album"`
	Subtitulo              string `json:"subtitulo,omitempty"`
	InterpretePrincipal    string `json:"interprete_principal,omitempty"`
	InterpretesInvitados   string `json:"interpretes_invitados,omitempty"`
	InterpreteParticipante string `json:"interprete_participante,omitempty"`
	SoporteFisico          string `json:"soporte_fisico,omitempty"`
	Editora                string `json:"editora,omitempty"`
	NumeroCatalogo         string `json:"numero_catalogo,omitempty"`
	CiudadEdicion          string `json:"ciudad_edicion,omitempty"`
	PaisEdicion            string `json:"pais_edicion,omitempty"`
	Year                   string `json:"year"`
	Pistas                 string `json:"pistas,omitempty"`
	Observaciones          string `json:"observaciones,omitempty"`
	Clasificacion          string `json:"clasificacion,omitempty"`
	Tema                   string `json:"tema,omitempty"`
}

type SongDetail struct {
	Song
	Lyrics string `json:"lyrics"`
}
