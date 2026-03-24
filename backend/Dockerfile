# Build stage
FROM golang:alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy the entire backend project
COPY backend/ ./backend/
COPY LetrasTXT/ ./LetrasTXT/
COPY datos.html ./datos.html

# Move into the backend directory to run Go commands
WORKDIR /app/backend
RUN go mod download

# 1. Build the database builder tool
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/db-builder ./cmd/build-db/main.go

# 2. Execute the tool to generate letras.db
WORKDIR /app
RUN ./db-builder -html datos.html -db letras.db

# 3. Build the main API binary
WORKDIR /app/backend
RUN go install github.com/swaggo/swag/cmd/swag@v1.16.6
RUN export PATH=$PATH:$(go env GOPATH)/bin && swag init -g main.go
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/main ./main.go

# 4. Build a tiny healthcheck binary (since distroless has no curl)
RUN echo 'package main; import ("net/http"; "os"); func main() { _, err := http.Get("http://localhost:8080/health"); if err != nil { os.Exit(1) }; os.Exit(0) }' > healthcheck.go
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/healthcheck healthcheck.go

# Run stage (Distroless)
FROM gcr.io/distroless/static-debian12

WORKDIR /app

# Copy the binary, the generated database, and the healthcheck tool
COPY --from=builder /app/main .
COPY --from=builder /app/letras.db .
COPY --from=builder /app/healthcheck .

USER nonroot:nonroot

EXPOSE 8080

CMD ["./main"]
