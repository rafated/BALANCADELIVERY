const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const port = 3000;

// Conectando ao banco de dados SQL
let db = new sqlite3.Database('/Users/matheusmarciano/Desktop/Estágio MCD/API_TEST/db_picklist.db', (err) => {
    if (err) {
        console.error('Erro ao conectar ao banco de dados:', err.message);
    } else {
        console.log('Conectado ao banco de dados SQLite.');
    }
});

// Middleware para lidar com JSON
app.use(express.json());

//Rota GET para buscar produtos com designação específica
app.get('/api/produtos', (req, res) => {
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

//Rota GET para buscar ingredientes por nome
app.get('/api/ingredientes', (req, res) => {
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

//Rota POST para inserir dados na tabela pick_list
app.post('/api/pick_list', (req, res) => {
    const { numero_pedido, list, file_name, estado } = req.body;

    const sql = `
        INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado) 
        VALUES (?, ?, ?, ?, ?)`;
    const params = [numero_pedido, list, file_name, estado, estado];

    db.run(sql, params, function(err) {
        if (err) {
            console.error('Erro ao inserir na pick_list:', err.message);
            res.status(500).json({ error: "Erro ao inserir dados na pick_list." });
        } else {
            
            res.status(201).json({ message: "Dados inseridos com sucesso.", id: this.lastID });
        }
    });
});

// Iniciando o servidor
app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
});
