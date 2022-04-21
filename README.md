# alertmanager-to-statuspage

Service to accept `alertmanager` web hooks and send alerts to `statuspage`

Example receiver:

```
receivers:
- name: my_statuspage
  webhook_configs:
    - url: http://alertmanager-to-statuspage:9647
```

## build

~~
docker login
docker-compose -f docker-compose-build.yml build
docker-compose -f docker-compose-build.yml push
~~

## configuration

customize your configuration via environment variables (see example in `docker-compose.yml`)

## run

~~
docker-compose up
~~

## prepare helm chart

~~
helm package examples/helmfile/alertmanager-to-statuspage/
mv alertmanager-to-statuspage-0.0.1.tgz charts/
helm repo index charts --url https://raw.githubusercontent.com/ivia/alertmanager-to-statuspage/main/charts/
~~
