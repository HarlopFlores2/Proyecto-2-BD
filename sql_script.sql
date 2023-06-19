-- sudo -i -u postgres
-- psql
-- create database proy2;
-- \c proy2

-- create table temp(data jsonb);
-- \copy temp(data) from '/tmp/newdata.json' csv quote e'\x01' delimiter e'\x02';
-- \dt



CREATE TABLE papers (
    id text NOT NULL PRIMARY KEY,
    abstract text NOT NULL
);

INSERT INTO papers
SELECT data->>'id', data->>'abstract'
FROM temp;

select id, abstract from papers limit 2;
select id, abstract from papers where id='0704.0001';
select count(*) from papers;


alter table papers
add column abstract_idx tsvector
generated always as (to_tsvector('english', abstract)) stored;

create index abstract_index on papers using gin (abstract_idx);

select id, abstract, ts_rank_cd(abstract_idx, query) as rank
from papers, plainto_tsquery('english', 'dimensionality reduction') query
where query @@ abstract_idx
order by rank desc
limit 3;