CREATE TABLE IF NOT EXISTS pokemon(
ID int,
Name varchar(30),
Type varchar(30),
HP int,
Att int,
Def int,
Height decimal,
Weight decimal,
CONSTRAINT pokemon_pk PRIMARY KEY (Name)
);

COPY pokemon(ID, Name, Type, HP, Att, Def, Height, Weight)
FROM '.../tmp/pokemon.csv'
DELIMITER ',' 
CSV HEADER;