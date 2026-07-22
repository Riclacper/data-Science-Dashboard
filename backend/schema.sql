CREATE TABLE IF NOT EXISTS ocorrencias (
    id BIGSERIAL PRIMARY KEY,
    "tipoCrime" VARCHAR(100) NOT NULL,
    status VARCHAR(100) NOT NULL,
    data DATE,
    hora TIME,
    descricao TEXT,
    "nomeVitima" VARCHAR(200),
    local VARCHAR(255),
    cidade VARCHAR(100) NOT NULL,
    uf VARCHAR(2) NOT NULL CHECK (char_length(uf) = 2),
    coordenadas VARCHAR(100),
    perito VARCHAR(200),
    fotos JSONB NOT NULL DEFAULT '[]'::jsonb,
    anexos JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ocorrencias_tipo_crime ON ocorrencias ("tipoCrime");
CREATE INDEX IF NOT EXISTS idx_ocorrencias_status ON ocorrencias (status);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_data ON ocorrencias (data);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_cidade ON ocorrencias (cidade);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_uf ON ocorrencias (uf);
