# WebSite de [Chaucha.party](https://chaucha.party/login)

En este sitio web, puedes enviar y recibir chauchas además de bloquear tus chauchas hasta cierto tiempo en el futuro.

Este proyecto utiliza dos proyectos previos generados en el Proyecto Chaucha. 

- [Check Lock Time Verify](https://github.com/proyecto-chaucha/CLTV): En este proyecto encontrarás información sobre cómo programar el *dinero* en chauchas. Si quieres dejar una herencia, éste es el proyecto que debes implementar.
- [Quirquincho](https://github.com/proyecto-chaucha/quirquincho): Quirquincho es un progama que permite crear direcciones chaucha, enviar y recibirlas mediante comandos en Telegram. La base es utilizada en este proyecto para generar las direcciones, además de enviar y recibir chauchas.


# Instalación

Sitio web creado en Python. La forma de ejecución local es la siguiente:

Instalamos paquetes python

```sh
sudo apt-get install python-setuptools python-dev build-essential.
```

Instalamos el lector QR (<- no funcionó)
```sh
pip install Flask-QRcode
```


Otra forma que tampoco funcionó
```sh
pip install -r requirements.txt --user

```



### Troubleshooting Flask-QRcode

Al intentar instalar el paquete anterior, puede darte el siguiente mensaje de error:
```
Could not install packages due to an EnvironmentError: [Errno 13] Permiso denegado: '/usr/local/lib/python2.7/dist-packages/Jinja2-2.10.dist-info'
Consider using the `--user` option or check the permissions.
```
La forma de instalar el paquete, es considerando la opcion **--user**. Así, le diremos al paquete que se instale dentro del espacio local de trabajo:

```sh
python -m pip install --user Flask-QRcode
```

De esta manera, el paquete queda guardado dentro de mi entorno local

```sh
/home/ignacio/.local/lib/python3.5/site-packages/
```

En la carpeta raíz, ejecutamos lo siguiente:
```sh
python3 __main__.py
```


Me aparece el siguiente error y no puedo continuar:

```sh
ignacio@ignacio-mint ~/Escritorio/Proyectos Independientes/Chaucha/chungungo $ python3 __main__.py
Traceback (most recent call last):
  File "__main__.py", line 2, in <module>
    from chungungo import app
  File "/home/ignacio/Escritorio/Proyectos Independientes/Chaucha/chungungo/chungungo/__init__.py", line 2, in <module>
    from flask_qrcode import QRcode
ImportError: No module named 'flask_qrcode'
```




