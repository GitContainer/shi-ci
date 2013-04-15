# configuration file for nginx with site: *.shi-ci.com

# http://shi-ci.com

server {

    listen        80;
    server_name   shi-ci.com;

    client_max_body_size 1m;

    rewrite ^(.*) http://www.shi-ci.com$1 permanent;

}

# http://www.shi-ci.com

server {

    listen      80;
    server_name www.shi-ci.com;

    root       /srv/www.shi-ci.com/www;
    access_log /var/log/nginx/www.shici.com-access.log;
    error_log  /var/log/nginx/www.shici.com-error.log;

    client_max_body_size 1m;

    gzip            on;
    gzip_min_length 1024;
    gzip_buffers    4 8k;
    gzip_types      text/css application/x-javascript application/json;

    sendfile on;

    location = /favicon.ico {
        root /srv/www.shi-ci.com/www;
    }

    location ^~ /static/ {
        root /srv/www.shi-ci.com/www;
    }

    location = /search {
        proxy_pass       http://127.0.0.1:8080;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass       http://127.0.0.1:9000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

}

# http://search.shi-ci.com

server {

    listen      80;
    server_name search.shi-ci.com;

    access_log /var/log/nginx/search.shici.com-access.log;
    error_log  /var/log/nginx/search.shici.com-error.log;

    client_max_body_size 1m;

    gzip            on;
    gzip_min_length 1024;
    gzip_buffers    4 8k;
    gzip_types      application/x-javascript application/json;

    sendfile on;

    location / {
        proxy_pass       http://127.0.0.1:8080;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

}
