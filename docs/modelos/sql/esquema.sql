-- =====================================================================
-- Sistema Digital de Juego de Cartas · Esquema relacional (PostgreSQL 16)
-- Entregable 2 · V-0.0.1.0 · Tercera forma normal (3FN)
-- Soporta partidas atómicas (Clásica 4-3-3: 1 ronda) y multironda (Apuntado a 101).
-- Agregar una variante NO cambia este esquema: se inserta una fila en `variante`
-- y sus parámetros van en `parametro_partida` (ADR-03 y ADR-04).
-- =====================================================================

CREATE TABLE jugador (
    jugador_id      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    alias           VARCHAR(30)   NOT NULL UNIQUE,
    correo          VARCHAR(120)  UNIQUE,
    creado_en       TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Sesión de conexión: permite reconectar al jugador si refresca el navegador.
CREATE TABLE sesion (
    sesion_id        UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    jugador_id       UUID          NOT NULL REFERENCES jugador (jugador_id),
    token_hash       CHAR(64)      NOT NULL UNIQUE,
    estado           VARCHAR(10)   NOT NULL DEFAULT 'ACTIVA'
                     CHECK (estado IN ('ACTIVA', 'CERRADA', 'EXPIRADA')),
    iniciada_en      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    ultima_actividad TIMESTAMPTZ   NOT NULL DEFAULT now(),
    expira_en        TIMESTAMPTZ   NOT NULL
);

CREATE TABLE sala (
    sala_id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_invitacion CHAR(6)      NOT NULL UNIQUE,
    anfitrion_id      UUID         NOT NULL REFERENCES jugador (jugador_id),
    capacidad         SMALLINT     NOT NULL CHECK (capacidad BETWEEN 2 AND 6),
    estado            VARCHAR(10)  NOT NULL DEFAULT 'ABIERTA'
                      CHECK (estado IN ('ABIERTA', 'EN_PARTIDA', 'CERRADA')),
    creada_en         TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Catálogo de plug-ins registrados. Al arrancar, el composition root entrega al repositorio
-- la lista que descubrió PluginRegistry y el adaptador hace el UPSERT (el registro no toca la base).
CREATE TABLE variante (
    variante_codigo  VARCHAR(30)  PRIMARY KEY,
    nombre           VARCHAR(60)  NOT NULL,
    version_plugin   VARCHAR(20)  NOT NULL,
    version_contrato VARCHAR(10)  NOT NULL,
    activa           BOOLEAN      NOT NULL DEFAULT TRUE,
    registrada_en    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE partida (
    partida_id      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    sala_id         UUID          NOT NULL REFERENCES sala (sala_id),
    variante_codigo VARCHAR(30)   NOT NULL REFERENCES variante (variante_codigo),
    estado          VARCHAR(12)   NOT NULL DEFAULT 'CONFIGURANDO'
                    CHECK (estado IN ('CONFIGURANDO', 'EN_CURSO', 'FINALIZADA')),
    iniciada_en     TIMESTAMPTZ,
    finalizada_en   TIMESTAMPTZ,
    ganador_id      UUID          REFERENCES jugador (jugador_id),
    CHECK ((estado = 'FINALIZADA') = (finalizada_en IS NOT NULL))
);
-- Una sala tiene como máximo una partida en curso.
CREATE UNIQUE INDEX ux_partida_en_curso_por_sala ON partida (sala_id) WHERE estado = 'EN_CURSO';

-- Configuración de la mesa: cada clave la declara el esquema del plug-in (esquema_configuracion()).
CREATE TABLE parametro_partida (
    partida_id  UUID         NOT NULL REFERENCES partida (partida_id) ON DELETE CASCADE,
    clave       VARCHAR(40)  NOT NULL,
    valor       VARCHAR(60)  NOT NULL,
    PRIMARY KEY (partida_id, clave)
);

CREATE TABLE participacion (
    partida_id      UUID         NOT NULL REFERENCES partida (partida_id),
    jugador_id      UUID         NOT NULL REFERENCES jugador (jugador_id),
    asiento         SMALLINT     NOT NULL CHECK (asiento BETWEEN 1 AND 6),
    estado_jugador  VARCHAR(12)  NOT NULL DEFAULT 'ACTIVO'
                    CHECK (estado_jugador IN ('ACTIVO', 'ELIMINADO', 'REINGRESADO', 'ABANDONO')),  -- ABANDONO: R-03 (sección 4.3)
    PRIMARY KEY (partida_id, jugador_id),
    UNIQUE (partida_id, asiento)
);

-- Marcador vigente por jugador en la partida (penalización neta acumulada; Apuntado a 101).
CREATE TABLE puntaje_acumulado (
    partida_id      UUID         NOT NULL,
    jugador_id      UUID         NOT NULL,
    total           INTEGER      NOT NULL DEFAULT 0,
    version         INTEGER      NOT NULL DEFAULT 0,
    actualizado_en  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (partida_id, jugador_id),
    FOREIGN KEY (partida_id, jugador_id) REFERENCES participacion (partida_id, jugador_id)
);

CREATE TABLE ronda (
    ronda_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    partida_id   UUID         NOT NULL REFERENCES partida (partida_id),
    numero       SMALLINT     NOT NULL CHECK (numero >= 1),
    estado       VARCHAR(10)  NOT NULL DEFAULT 'EN_JUEGO'
                 CHECK (estado IN ('EN_JUEGO', 'LIQUIDADA', 'ANULADA')),
    semilla      BIGINT       NOT NULL,
    iniciada_en  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    cerrada_en   TIMESTAMPTZ,
    cerrada_por  UUID,
    tipo_cierre  VARCHAR(20),                       -- código definido por el plug-in (TOCAR, PINTAS, ...): sin CHECK fijo (ADR-03)
    UNIQUE (partida_id, numero),
    FOREIGN KEY (partida_id, cerrada_por) REFERENCES participacion (partida_id, jugador_id),
    CHECK ((estado = 'LIQUIDADA') = (cerrada_por IS NOT NULL AND tipo_cierre IS NOT NULL AND cerrada_en IS NOT NULL))
);
-- Como máximo una ronda abierta por partida.
CREATE UNIQUE INDEX ux_ronda_abierta_por_partida ON ronda (partida_id) WHERE estado = 'EN_JUEGO';

-- Catálogo fijo de 54 cartas por mazo (52 + 2 comodines).
CREATE TABLE carta (
    carta_codigo  VARCHAR(3)  PRIMARY KEY,            -- 'AH', '10S', 'KD', 'JK1', 'JK2'
    rango         SMALLINT    CHECK (rango BETWEEN 1 AND 13),
    pinta         CHAR(1)     CHECK (pinta IN ('H', 'D', 'C', 'S')),
    CHECK ((rango IS NULL) = (pinta IS NULL))         -- comodín: sin rango ni pinta
);

CREATE TABLE mano_jugador (
    mano_id     UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
    ronda_id    UUID  NOT NULL REFERENCES ronda (ronda_id),
    jugador_id  UUID  NOT NULL REFERENCES jugador (jugador_id),
    UNIQUE (ronda_id, jugador_id)
);

-- Composición actual de cada mano (se actualiza en la misma transacción que la jugada).
CREATE TABLE carta_mano (
    mano_id       UUID        NOT NULL REFERENCES mano_jugador (mano_id) ON DELETE CASCADE,
    carta_codigo  VARCHAR(3)  NOT NULL REFERENCES carta (carta_codigo),
    mazo_numero   SMALLINT    NOT NULL CHECK (mazo_numero >= 1),
    PRIMARY KEY (mano_id, carta_codigo, mazo_numero)
);

-- Bitácora inmutable de jugadas: trazabilidad de robos, descartes y cierres.
CREATE TABLE turno_jugada (
    jugada_id       BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mano_id         UUID         NOT NULL REFERENCES mano_jugador (mano_id),
    numero_turno    INTEGER      NOT NULL CHECK (numero_turno >= 1),
    accion          VARCHAR(16)  NOT NULL CHECK (accion IN
                    ('ROBAR_MAZO', 'ROBAR_DESCARTE', 'DESCARTAR', 'SOLICITAR_CIERRE', 'TIEMPO_AGOTADO')),
    carta_codigo    VARCHAR(3)   REFERENCES carta (carta_codigo),
    mazo_numero     SMALLINT     CHECK (mazo_numero >= 1),
    resultado       VARCHAR(10)  NOT NULL CHECK (resultado IN ('ACEPTADA', 'RECHAZADA')),
    motivo_rechazo  VARCHAR(200),
    comando_id      UUID         NOT NULL UNIQUE,     -- idempotencia: un comando reintentado no se aplica dos veces
    ocurrida_en     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK ((accion IN ('ROBAR_MAZO', 'ROBAR_DESCARTE', 'DESCARTAR')) = (carta_codigo IS NOT NULL)),
    CHECK ((carta_codigo IS NULL) = (mazo_numero IS NULL)),
    CHECK ((resultado = 'RECHAZADA') = (motivo_rechazo IS NOT NULL))
);
CREATE INDEX ix_turno_jugada_mano ON turno_jugada (mano_id, jugada_id);

-- Historial de penalizaciones: una fila por jugador y ronda liquidada.
CREATE TABLE puntaje_ronda (
    ronda_id      UUID      NOT NULL REFERENCES ronda (ronda_id),
    jugador_id    UUID      NOT NULL REFERENCES jugador (jugador_id),
    penalizacion  SMALLINT  NOT NULL CHECK (penalizacion >= 0),
    bonificacion  SMALLINT  NOT NULL DEFAULT 0 CHECK (bonificacion >= 0),
    PRIMARY KEY (ronda_id, jugador_id)                -- impide liquidar dos veces la misma ronda
);

-- Vistas de consulta
CREATE VIEW v_historial_puntajes AS
SELECT r.partida_id, r.numero, pr.jugador_id, pr.penalizacion, pr.bonificacion,
       pr.penalizacion - pr.bonificacion AS delta,
       SUM(pr.penalizacion - pr.bonificacion) OVER (PARTITION BY r.partida_id, pr.jugador_id ORDER BY r.numero) AS acumulado
FROM puntaje_ronda pr JOIN ronda r USING (ronda_id);

-- Fitness function de datos: debe devolver 0 filas (el marcador materializado coincide con el historial).
CREATE VIEW v_inconsistencias_marcador AS
SELECT pa.partida_id, pa.jugador_id, pa.total, COALESCE(SUM(pr.penalizacion - pr.bonificacion), 0) AS suma_historial
FROM puntaje_acumulado pa
LEFT JOIN ronda r ON r.partida_id = pa.partida_id
LEFT JOIN puntaje_ronda pr ON pr.ronda_id = r.ronda_id AND pr.jugador_id = pa.jugador_id
GROUP BY pa.partida_id, pa.jugador_id, pa.total
HAVING pa.total <> COALESCE(SUM(pr.penalizacion - pr.bonificacion), 0);
