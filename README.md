# PForm 

## Context

In our academic year project we worked on setting up a vulnerable environment to show case some commun vulnrabilities and their impact .

In this project we developed and created some [custom tools](https://github.com/OussemaJaouadi/PFTools) that we needed .

The academic project report is uploaded ( but in french ) 

The describtion and configuration below demonstrates how we setup our environment and running the application using NGINX as reverse proxy .

## Description 

A plateform for "Project du Fin d'année" projects

* Students create accounts and can ask for new role .
* Students can upload their project report when assigned to project .
* Teachers create project and and assign students to it .
* Teachers creates sprints for each project .
* Admins can approve role changing requests .
* Teachers and admins have monitoring scripts .

## Serve the application using Gunicorn and NGINX

1. Install an iso (Debian/Ubuntu)
2. Install Virtual Box
3. Create Nat Network
4. Create VM
5. Install the iso os on VM
6. Configure Nat Network on VM ( make sur our attacking machine is on same NAT Network as the vulnrable machine )
7. Add those configuration to the VM : 
   ```bash
        sudo apt update
        sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools
        sudo apt install ufw
        sudo apt install python3-venv
        git clone https://github.com/OussemaJaouadi/PForm
        cd PForm
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        nano .env # PORT=<port> , SECRET=<jwt_secrets>
        deactivate
        pip install wheel
        source venv/bin/activate
        pip install gunicorn flask 
        sudo ufw allow <port>
        python app.py # Now we tested the app 
    ```
    > We can always exit the app using `CTRL + C`
8. Creating an WSGI entry point : 
    ```bash
        nano ~/PForm/wsgi.py
    ```
    And add this code :

    ```python
    from app import app
    if __name__ == "__main__":
        app.run()
    ```
    We save the file and go back to the terminal 
9. Configuring UWSGI and creating a systemd Unit File : 
    ```bash
    uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app
    ```
    Until now we can still visit our web appliciation through `http://<vm_ip>:<port>/`

    We  go back to the terminal and run :
    ```bash
    sudo nano /etc/systemd/system/app.service
    ```
    And add this code :
    ```ini
    [Unit]
    Description=Gunicorn instance to serve PForm
    After=network.target

    [Service]
    User=<Username>
    Group=www-data
    WorkingDirectory=/home/<Username>/PForm
    Environment="PATH=/home/<Username>/PForm/venv/bin"
    ExecStart=/home/<Username>/PForm/venv/bin/gunicorn --workers 3 --bind unix:form.sock wsgi:app

    [Install]
    WantedBy=multi-user.target
    ```	

    With that, your systemd service file is complete. Save and close it now.

    Before starting the guinicorn service, you’ll need to make a permission change, because the Nginx www-data user won’t be able to read files in your home directory by default . A quick fix is to change the group associated with your home directory using chgrp:

    ```bash	
    sudo chgrp www-data /home/<User>
    ```

    You can now start the gunicorn service you created:

    ```bash
    sudo systemctl start app
    ```	
    Then enable it so that it starts at boot:

    ```bash
    sudo systemctl enable app
    ```

    Check the status of the process to find out whether it was able to start:

    ```bash
    sudo systemctl status app
    ```

10. Configuring Nginx to Proxy Requests : 

    ```bash
    sudo nano /etc/nginx/sites-available/app
    ```
    And add this code :

    ```nginx
    http {
        upstream backend {
        server unix:/home/<Username>/PForm/form.sock;
    }

    server {
        listen 80;
        server_name form.local;

        location / {
        include uwsgi_params;
        uwsgi_pass backend;
        }
    }
    }
    ```	

    Save and close the file then , to enable the Nginx server block configuration we’ve just created, link the file to the sites-enabled directory:

    ```bash
    sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
    ```

    Then we unlink the default configuration file from the /sites-enabled/ directory:

    ```bash
    sudo unlink /etc/nginx/sites-enabled/default
    ```

    And we test and restart Nginx :

    ```bash	
    sudo nginx -t
    sudo systemctl restart nginx
    ```

    Finally, adjust the firewall once again. You no longer need access through our port, so you can remove that rule. Then, you can allow access to the Nginx server:

    ```bash
    sudo ufw delete allow <port>
    sudo ufw allow 'Nginx Full'
    ```

    > Some Trouble shooting : <br>
    >When testing if the app is running or not we will get `502 Bad Gateway` error , to fix that we need to check the logs :
    > ```bash
    > sudo chown www-data:www-data /home/<Username>/PForm/form.sock
    > sudo chmod +x /home/<Username>/
    > sudo systemctl restart app
    > sudo systemctl restart nginx
    > ```
