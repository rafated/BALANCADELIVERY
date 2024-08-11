//Define e importa o modulos necesarios para a execução do codigo
const express = require('express');
const body_parser = require('body-parser');


//Cria uma instancia da aplicação express
const app = express();
const port = process.env.PORT || 3000;

//--------------------------------------------------------
//POST REQUEST
app.use(body_parser.json());

app.post('/register', (req, res) => {
    const { username, password } = req.body;
    console.log(`username: ${username} password: ${password}`);
    res.json({message: 'Dados recebidos com sucesso!', dadosRecebidos: req.body});
});
//--------------------------------------------------------
//GET REQUEST
app.get('/login', (req, res) => {
    const { username, password } = req.query;
    console.log(`username: ${username} password: ${password}`);
    res.json({ message: 'Autenticado com sucesso!', dadosRecebidos: req.query});
});

app.listen(port , () => {
    console.log(`Server is running on port ${port}`);
});

/*
Vamos definit uma rota para teste de resquests
app.get('/', (req, res) => {
    res.send('Hello, express!');
});

const data = {
    name: 'John Doe',
    age: 30,
    email: 'johndoe@example.com'
};

app.get('/resgiter', (req, res) => {
    res.send(data);
});
*/
