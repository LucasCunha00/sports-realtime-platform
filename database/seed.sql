INSERT INTO teams (name, short_name, country, stadium) VALUES
    ('Manchester City',   'MCI', 'England', 'Etihad Stadium'),
    ('Arsenal',           'ARS', 'England', 'Emirates Stadium'),
    ('Real Madrid',       'RMA', 'Spain',   'Santiago Bernabéu'),
    ('Barcelona',         'BAR', 'Spain',   'Spotify Camp Nou'),
    ('Bayern Munich',     'BAY', 'Germany', 'Allianz Arena'),
    ('Borussia Dortmund', 'BVB', 'Germany', 'Signal Iduna Park'),
    ('PSG',               'PSG', 'France',  'Parc des Princes'),
    ('Inter Milan',       'INT', 'Italy',   'San Siro')
ON CONFLICT DO NOTHING;

INSERT INTO players (team_id, name, position, number, nationality) VALUES
    -- Manchester City (1)
    (1, 'Ederson',          'GK',  31, 'Brazil'),
    (1, 'Rúben Dias',       'DEF',  3, 'Portugal'),
    (1, 'Rodri',            'MID', 16, 'Spain'),
    (1, 'Kevin De Bruyne',  'MID', 17, 'Belgium'),
    (1, 'Erling Haaland',   'FWD',  9, 'Norway'),
    -- Arsenal (2)
    (2, 'David Raya',       'GK',  22, 'Spain'),
    (2, 'William Saliba',   'DEF', 12, 'France'),
    (2, 'Martin Ødegaard',  'MID',  8, 'Norway'),
    (2, 'Bukayo Saka',      'FWD',  7, 'England'),
    (2, 'Gabriel Martinelli','FWD', 11, 'Brazil'),
    -- Real Madrid (3)
    (3, 'Thibaut Courtois', 'GK',  1, 'Belgium'),
    (3, 'Dani Carvajal',    'DEF',  2, 'Spain'),
    (3, 'Luka Modric',      'MID', 10, 'Croatia'),
    (3, 'Jude Bellingham',  'MID',  5, 'England'),
    (3, 'Vinícius Jr.',     'FWD', 20, 'Brazil'),
    -- Barcelona (4)
    (4, 'Marc-André ter Stegen','GK', 1, 'Germany'),
    (4, 'Ronald Araújo',    'DEF',  4, 'Uruguay'),
    (4, 'Pedri',            'MID',  8, 'Spain'),
    (4, 'Gavi',             'MID',  6, 'Spain'),
    (4, 'Robert Lewandowski','FWD', 9, 'Poland')
ON CONFLICT DO NOTHING;