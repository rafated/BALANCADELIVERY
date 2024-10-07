const https = require('https');
const fs = require('fs');
const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const { body, query, validationResult } = require('express-validator');
require('dotenv').config();  // Carregar variáveis de ambiente do arquivo .env

// API Key do servidor a partir da variável de ambiente
const API_KEY = process.env.API_KEY;

const app = express();
const port = process.env.PORT || 3000;  // Usa a porta do .env ou 3000 como fallback

// Carregar certificados SSL
const privateKey = fs.readFileSync('C:/Users/Uber/Desktop/API/server.key', 'utf8');
const certificate = fs.readFileSync('C:/Users/Uber/Desktop/API/server.cert', 'utf8');

const credentials = {
    key: privateKey,
    cert: certificate,
    };

// Conectando ao banco de dados SQLite
let db = new sqlite3.Database('C:/Users/Uber/Desktop/API/db_picklist.db', (err) => {
    if (err) {
        console.error('Erro ao conectar ao banco de dados:', err.message);
    } else {
        console.log('Conectado ao banco de dados SQLite.');
    }
});

// Middleware para segurança
app.use(helmet());

// Middleware para limitar requisições (Rate Limiting)
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: 20000 // Limita cada IP a 2000 requisições por janela de 15 minutos
});
app.use(limiter);

// Middleware para lidar com JSON
app.use(express.json());

// Middleware para configurar CORS
const corsOptions = {
    origin: 'https://85.246.46.140',
    optionsSuccessStatus: 200
};
app.use(cors(corsOptions));

// Middleware para verificar API Key
function checkApiKey(req, res, next) {
    const clientApiKey = req.headers['x-api-key'];

    if (clientApiKey && clientApiKey === API_KEY) {
        return next(); // Se a chave for válida, prossiga com a requisição
    }

    res.status(403).json({ message: 'Acesso negado. Chave de API inválida.' });
}

// Rota pública (não requer API Key)
app.get('/api', (req, res) => {
    res.status(200).json({ message: 'API is online' });
});

//----------------------------ROTAS PROTEGIDAS COM API KEY----------------------------------
// Todas as rotas abaixo agora requerem uma API Key válida para serem acessadas

// Rota GET para buscar produtos com designação específica
app.get('/api/produtos', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    
    const name = req.query.name;
    const sql = `
        SELECT * FROM produtos 
        INNER JOIN designacao ON designacao.produto_id = produtos.produto_id 
        WHERE designacao.nome = ?`;

    db.all(sql, [name], (err, rows) => {
        if (err) {
            console.error('Erro ao buscar produtos:', err.message);
            res.status(500).json({ error: "Erro ao buscar produtos." });
        } else {
            console.log('Dados retornados com sucesso: ', rows);
            res.json(rows);
        }
    });
});

// Rota GET para buscar ingredientes por nome
app.get('/api/ingredientes', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const name = req.query.name;
    const sql = "SELECT * FROM ingredientes WHERE nome = ?";

    db.all(sql, [name], (err, rows) => {
        if (err) {
            console.error('Erro ao buscar ingredientes:', err.message);
            res.status(500).json({ error: "Erro ao buscar ingredientes." });
        } else {
            console.log('Dados retornados com sucesso: ', rows);
            res.json(rows);
        }
    });
});

// Rota POST para inserir dados na tabela pick_list
app.post('/api/pick_list', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const { numero_pedido, list, file_name, estado, pendente, codigo_restaurante, time_stamp} = req.body;

    const sql = `
        INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado, pendente, codigo_restaurante, time_stamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`;
    const params = [numero_pedido, list, file_name, estado, estado, pendente, codigo_restaurante, time_stamp];

    db.run(sql, params, function(err) {
        if (err) {
            console.error('Erro ao inserir na pick_list:', err.message);
            res.status(500).json({ error: "Erro ao inserir dados na pick_list." });
        } else {
            res.status(201).json({ message: "Dados inseridos com sucesso.", id: this.lastID });
        }
    });
});

// Rota GET para buscar o estado de um pedido específico
app.get('/api/pedido/estado', checkApiKey, (req, res) => {
    const pedido = req.query.pedido;
    const rest_code = req.query.rest_code;

    const sql = `SELECT state, confirmado FROM pick_list WHERE delivery_name = ? 
    AND codigo_restaurante = ? 
    ORDER BY id DESC LIMIT 1`;

    db.get(sql, [pedido, rest_code], (err, row) => {
        if (err) {
            console.error('Erro ao buscar o estado do pedido:', err.message);
            res.status(500).json({ error: "Erro ao buscar o estado do pedido." });
        } else {
            if (row) {
                res.json(row);
            } else {
                res.status(404).json({ message: "Pedido não encontrado." });
            }
        }
    });
});

// Rota GET para retornar o último pedido de cada restaurante
app.get('/api/pedidos/ultimo', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const rest_code = req.query.rest_code;
    
    const sql = `
        SELECT * FROM pick_list 
        WHERE state = 0 AND codigo_restaurante = ?
        ORDER BY id DESC 
        LIMIT 1`;

    db.get(sql, [rest_code], (err, row) => {
        if (err) {
            console.error('Erro ao buscar o último pedido:', err.message);
            return res.status(500).json({ error: "Erro ao buscar o último pedido." });
        }

        if (row) {
            res.json(row);
            console.log('Pedido retornado com sucesso');
        } else {
            res.status(404).json({ message: "Nenhum pedido encontrado." });
        }
    });
});

// Rota POST para confirmar o estado do pedido pelo número (state = 1)
app.post('/api/pedido/confirmar_estado', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const rest_code = req.query.rest_code;
    const pedido = req.query.pedido;

    const sql = `
        UPDATE pick_list 
        SET state = 1 
        WHERE delivery_name = ? AND codigo_restaurante = ?`;

    db.run(sql, [pedido, rest_code], function(err) {
        if (err) {
            console.error('Erro ao confirmar o pedido:', err.message);
            res.status(500).json({ error: "Erro ao confirmar o pedido." });
        } else {
            res.json({ message: "Pedido confirmado com sucesso." });
        }
    });
});

// Rota GET para buscar detalhes de um pedido específico
app.get('/api/pedidos/detalhes', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const pedido = req.query.pedido;
    const rest_code = req.query.rest_code;

    const sql = "SELECT * FROM pick_list WHERE delivery_name = ? AND codigo_restaurante = ? ORDER BY id DESC LIMIT 1";

    db.get(sql, [pedido, rest_code], (err, row) => {
        if (err) {
            console.error('Erro ao buscar detalhes do pedido:', err.message);
            res.status(500).json({ error: "Erro ao buscar detalhes do pedido." });
        } else {
            if (row) {
                res.json(row);
                console.log('Detalhes do pedido retornados com sucesso:', row);
            } else {
                res.status(404).json({ message: "Pedido não encontrado." });
            }
        }
    });
});

// Rota POST para confirmar o pedido pelo número (confirmado = 1)
app.post('/api/pedido/confirmar', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const rest_code = req.query.rest_code;
    const pedido = req.query.pedido;

    const sql = `
        UPDATE pick_list 
        SET confirmado = 1 
        WHERE id = (
            SELECT id 
            FROM pick_list 
            WHERE delivery_name = ? AND codigo_restaurante = ? 
            ORDER BY id DESC 
            LIMIT 1
        )`;

    db.run(sql, [pedido, rest_code], function(err) {
        if (err) {
            console.error('Erro ao confirmar o pedido:', err.message);
            res.status(500).json({ error: "Erro ao confirmar o pedido." });
        } else {
            res.json({ message: "Pedido confirmado com sucesso." });
        }
    });
});

// Rota POST para inserir dados na tabela pesagem
app.post('/api/pesagem', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const { pick_list_id, peso_estimado, peso_real, photo, start_time_stamp, end_time_stamp, tentativas} = req.body;

    const sql = `
        INSERT INTO pesagem (pick_list_id, peso_estimado, peso_real, photo, start_time_stamp, end_time_stamp, tentativas) 
        VALUES (?, ?, ?, ?, ?, ?, ?)`;
    const params = [pick_list_id, peso_estimado, peso_real, photo, start_time_stamp, end_time_stamp, tentativas];

    db.run(sql, params, function(err) {
        if (err) {
            console.error('Erro ao inserir na tabela pesagem:', err.message);
            res.status(500).json({ error: "Erro ao inserir dados na tabela pesagem." });
        } else {
            res.status(201).json({ message: "Dados inseridos com sucesso na tabela pesagem.", id: this.lastID });
        }
    });
});

// Rota POST para sincronizar dados da tabela pick_list
app.post('/api/sync_pick_list', checkApiKey, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    const items = req.body.items;

    // Iniciar uma transação
    db.serialize(() => {
        db.run("BEGIN TRANSACTION");

        const sql = `
            UPDATE pick_list 
            SET pendente = 0 
            WHERE delivery_name = ?`;

        for (const item of items) {
            db.run(sql, [item.delivery_name], (err) => {
                if (err) {
                    console.error('Erro ao atualizar a pick_list:', err.message);
                    res.status(500).json({ error: "Erro ao atualizar dados na pick_list." });
                    db.run("ROLLBACK");
                    return;
                }
            });
        }

        // Comitar a transação após as atualizações
        db.run("COMMIT", (err) => {
            if (err) {
                console.error('Erro ao confirmar a transação:', err.message);
                res.status(500).json({ error: "Erro ao confirmar a transação de atualização." });
            } else {
                res.status(200).json({ message: "Dados sincronizados com sucesso." });
            }
        });
    });
});

// Rota POST para limpar os pedidos (por exemplo, marcar todos como confirmados)
app.post('/api/pedidos/limpar', checkApiKey, (req, res) => {
    
    const rest_code = req.body.rest_code;

    const sql = `
        UPDATE pick_list 
        SET confirmado = 1, state = 1 
        WHERE (confirmado = 0 OR state = 0) AND codigo_restaurante = ?`;
    
    db.run(sql, [rest_code], function(err) {
        if (err) {
            console.error('Erro ao limpar pedidos:', err.message);
            res.status(500).json({ error: "Erro ao limpar pedidos." });
        } else {
            res.json({ message: "Pedidos limpos com sucesso." });
        }
    });
});

// Criar servidor HTTPS
https.createServer(credentials, app).listen(port, () => {
    console.log(`Servidor rodando em https://85.246.46.140:${port}`);
});
