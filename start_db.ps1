docker run -d `
  --name chessinsight-postgres `
  -e POSTGRES_USER=chess `
  -e POSTGRES_PASSWORD=chess_pass `
  -e POSTGRES_DB=chess_trainer_db `
  -v chessinsightai_chess_pgdata:/var/lib/postgresql/data `
  -p 5434:5432 `
  postgres:13