import requests

#GET request method
response = requests.get('http://localhost:3000/login')
text = response.content.decode('utf-8')
print(text)


#POST request method
data = {
    'username': 'John Doe',
    'password': 'password123'
}
response = requests.post('http://localhost:3000/register', json=data)

#Quando enviamos uma request para o servidor o mesmo retorna um código no qual diz se a operção fi feita de forma correta
#Dicionário de códigos:
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
print('Status code: ', response.status_code)