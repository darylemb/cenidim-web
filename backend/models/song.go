package models

type Song struct {
	ID       int    `json:"id"`
	Title    string `json:"title"`
	Album    string `json:"album"`
	Filename string `json:"filename"`
}

type SongDetail struct {
	Song
	Lyrics string `json:"lyrics"`
}
