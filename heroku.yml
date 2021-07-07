setup:
  addons:
    - plan: heroku-postgresql
      as: db
build:
  docker:
    web: Dockerfile
run:
    web: bash start.sh
