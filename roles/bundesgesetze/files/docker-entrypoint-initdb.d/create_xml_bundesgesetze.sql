CREATE USER haex SUPERUSER;

CREATE SCHEMA bundesgesetze;

CREATE TABLE
  IF NOT EXISTS bundesgesetze.books (
    id SERIAL,
    amtabk text,
    jurabk text,
    updated_at date,
    description text,
    PRIMARY KEY (id)
  );

CREATE TABLE
  IF NOT EXISTS bundesgesetze.paragraphs (
    book_id integer REFERENCES bundesgesetze.books (id),
    enbez text,
    markdown text,
    PRIMARY KEY (book_id, enbez)
  );