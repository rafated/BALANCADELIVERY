const https = require('https');
const fs = require('fs');
const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const { body, query, validationResult } = require('express-validator');

const app = express();
const port = 3000;

// Carregar certificados SSL
const privateKey = fs.readFileSync('C:/Users/Uber/Desktop/API/server.key', 'utf8');
const certificate = fs.readFileSync('C:/Users/Uber/Desktop/API/server.cert/', 'utf8');

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
    max: 1000 // Limita cada IP a 100 requisições por janela de 15 minutos
});
app.use(limiter);

// Middleware para lidar com JSON
app.use(express.json());

// Middleware para configurar CORS
const corsOptions = {
    origin: 'https://85.246.46.140', // Substitua pelo domínio permitido
    optionsSuccessStatus: 200
};
app.use(cors(corsOptions));

app.get('/api', (req, res) => {
    res.status(200).json({ message: 'API is online' });
  });

// Rota GET para buscar produtos com designação específica
app.get('/api/produtos',
    //query('name').isString().trim().escape(),  // Validação e sanitização do parâmetro "name"
    (req, res) => {
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
    }
);

// Rota GET para buscar ingredientes por nome
app.get('/api/ingredientes',
       (req, res) => {
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
    }
);

// Rota POST para inserir dados na tabela pick_list
app.post('/api/pick_list',
    (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }

        const { numero_pedido, list, file_name, estado, pendente } = req.body;

        const sql = `
            INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado, pendente) 
            VALUES (?, ?, ?, ?, ?, ?)`;
        const params = [numero_pedido, list, file_name, estado, estado, pendente];

        db.run(sql, params, function(err) {
            if (err) {
                console.error('Erro ao inserir na pick_list:', err.message);
                res.status(500).json({ error: "Erro ao inserir dados na pick_list." });
            } else {
                res.status(201).json({ message: "Dados inseridos com sucesso.", id: this.lastID });
            }
        });
    }
);

// Rota GET para buscar o último pedido não confirmado (GUIPESAGEM)
app.get('/api/pedidos/ultimo', (req, res) => {
    const sql = `
        SELECT * FROM pick_list 
        WHERE state = 0 
        ORDER BY id DESC 
        LIMIT 1`;

    db.get(sql, [], (err, row) => {
        if (err) {
            console.error('Erro ao buscar o último pedido:', err.message);
            res.status(500).json({ error: "Erro ao buscar o último pedido." });
        } else {
            if (row) {
                res.json(row);
            } else {
                res.status(404).json({ message: "Nenhum pedido encontrado." });
            }
        }
    });
});

// Rota POST para confirmar um pedido (GUIPESAGEM)
app.post('/api/pedidos/:pedido/confirmar', (req, res) => {
    const pedido = req.params.pedido;
    const sql = `
        UPDATE pick_list 
        SET state = 1, confirmado = 1 
        WHERE delivery_name = ?`;

    db.run(sql, [pedido], function(err) {
        if (err) {
            console.error('Erro ao confirmar o pedido:', err.message);
            res.status(500).json({ error: "Erro ao confirmar o pedido." });
        } else {
            res.json({ message: "Pedido confirmado com sucesso." });
        }
    });
});

// Rota POST para sincronizar dados da tabela pick_list
app.post('/api/sync_pick_list', 
    body('items').isArray(), // Validação: verificar se 'items' é um array
    (req, res) => {
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
    }
);



// Criar servidor HTTPS
https.createServer(credentials, app).listen(port, () => {
    console.log(`Servidor rodando em https://85.246.46.140:${port}`);
});
