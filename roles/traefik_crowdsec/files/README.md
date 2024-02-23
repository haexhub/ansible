## Zielsetzung

Traefik v2 installieren und konfigurieren
Crowdsec installieren und konfigurieren
Traefik Services via CrowdSec sichern
Einzelner Stack
Wie wir unsere Services mit Traefik verfügbar machen

## TLDR

```
git clone git@github.com:haexhub/traefik-crowdsec-stack.git
```

```
chmod 600 /opt/containers/traefik-crowdsec-stack/traefik/{acme_letsencrypt.json,tls_letsencrypt.json}
```

```
vim traefik/traefik.yml
```

Mail Adressen für http resolver und tls resolver anpassen

```
docker compose up crowdsec -d && docker compose down
```

Füge folgendes zu crowdsec/config/acquis.yaml hinzu

```
---
filenames:
  - /var/log/traefik/*.log
labels:
  type: traefik
---
```

```
# cd /opt/containers/traefik-crowdsec-stack
docker compose up crowdsec -d
docker compose exec -t crowdsec cscli bouncers add traefik-crowdsec-bouncer
docker compose down
```

So, oder so ähnlich sollte die Ausgabe aussehen:

```
Api key for 'traefik-crowdsec-bouncer':

   ee21c448d67e04550dec5b07b42ad6ee

Please keep this key since you will not be able to retrieve it!
```

```
vim config/traefik-crowdsec-bouncer.env
```

Füge den generierten Schlüssel (in diesem Beispiel: ee21c448d67e04550dec5b07b42ad6ee) in unsere config/traefik-crowdsec-bouncer.env ein.

Unblock banned ip

```
docker compose exec -t crowdsec cscli decisions delete -i
```

## Voraussetzung

Docker mit Docker Compose installiert

## Traefik + CrowdSec im Stack vorbereiten

In dieser aktualisierten Anleitung konzentrieren wir uns darauf, Traefik, CrowdSec und alle damit verbundenen Komponenten in einem einzigen Stack zu definieren. Warum? Ganz einfach, die Erfahrung hat gezeigt, dass die Startreihenfolge der Container durchaus relevant sein kann. Mit einem Full-Stack-Ansatz kann ich diesen Aspekt besser steuern und somit eine optimale Performance und Funktionalität gewährleisten.

## clone Repository

Wir wechseln in das Verzeichnis `/opt/containers` und führen `git clone git@github.com:haexhub/traefik-crowdsec-stack.git` aus.

Als nächstes möchten wir sicherstellen, dass alles korrekt angelegt wurde. Hierfür verwenden wir den tree Befehl. Falls das tree Programm noch nicht installiert ist, können wir es wie folgt installieren:

```
sudo apt install tree
```

Jetzt können wir den Befehl tree Verzeichnis ausführen:

```
tree -L 2 -a /opt/containers/traefik-crowdsec-stack/
```

um die Struktur zu überprüfen. Die Ausgabe sollte folgendermaßen aussehen:

```
.
├── config
│   ├── crowdsec.env
│   ├── traefik.env
│   └── traefik-crowdsec-bouncer.env
├── crowdsec
│   ├── config
│   └── data
├── .env
└── traefik
    ├── acme_letsencrypt.json
    ├── dynamic_conf.yml
    ├── tls_letsencrypt.json
    └── traefik.yml
```

Jetzt müssen nur nur die Berechtigungen richtig gesetzte werden:

```
chmod 600 /opt/containers/traefik-crowdsec-stack/traefik/{acme_letsencrypt.json,tls_letsencrypt.json}
```

## DOTENV Konfiguration

Kopiere die die .env.example Datei und benne sie zu .env um. Anschließend muss diese noch etwas angepasst werden.
Bis auf eine Ausnahme ist dieses Beispielsetup bereits optimiert und erfordert keine weiteren Anpassungen, um richtig zu funktionieren. Die einzige Zeile, die du anpassen musst, ist `TRAEFIK_LABELS_TRAEFIK_HOST`. Hier definierst du die eigene Domain für das Traefik-Dashboard. Denke daran,`traefik.DeineDomainHier.de` durch die tatsächliche Domain zu ersetzen, welche auch via A oder CNAME auf den richtigen Server zeigt, die du für das Traefik-Dashboard verwenden möchtest.

Achtung! Die `` sind unabdingbar! Hier könnten aber auch mehrere Domains definiert werden:

```
TRAEFIK_LABELS_TRAEFIK_HOST=`traefik.DeineDomainHier.de`,`www.traefik.DeineDomainHier.de`
```

## Traefik-Konfiguration

Jetzt widmen wir uns der Konfigurationsdatei traefik.yml. In dieser Datei setzen wir statische Konfigurationsoptionen fest.
Beachte bitte, dass du die E-Mail-Adressen unter certificatesResolvers zwei mal anpasst. Sie dienen als Kontaktinformationen für Let’s Encrypt und sollten daher auf eine gültige E-Mail-Adresse gesetzt sein, die du kontrollierst.

Hinweis! An dieser Stelle darf nur eine E-Mail-Adresse gesetzt werden. Zwei unterschiedliche führen zu einem Fehler:

```
traefik.go:81: command traefik error: unable to initialize certificates resolver "tls_resolver", all the acme resolvers must use the same email
```

## CrowdSec-Konfiguration

Die config/traefik-crowdsec.env ist bereits gesetzt. Hier eine kurze Erklärung dazu:

- PGID: Dies steht für “Group ID” und bestimmt, unter welcher Gruppen-ID der CrowdSec-Prozess ausgeführt wird. Im vorliegenden Fall ist das die Gruppen-ID “1000”. Die Gruppen-ID sollte der ID einer existierenden Gruppe in deinem System entsprechen, die die benötigten Zugriffsrechte hat.
- COLLECTIONS: Dies ist eine Liste von sogenannten “Collection”-Namen. Eine Collection in CrowdSec ist eine Gruppe von Szenarien, Parsern und Post-Overflows, die einen bestimmten Zweck erfüllen. Im vorliegenden Fall werden die folgenden Collections verwendet:
- crowdsecurity/traefik: Diese Collection ist speziell für die Überwachung und den Schutz von Traefik, einem modernen Reverse-Proxy und Load-Balancer.
- crowdsecurity/http-cve: Diese Collection enthält Szenarien zur Erkennung von bekannten Schwachstellen und Angriffen (CVEs) auf HTTP-Server.-
- crowdsecurity/whitelist-good-actors: Eine Collection, die dafür sorgt, dass bekannte “gute” Akteure nicht fälschlicherweise als bösartig erkannt werden.
- crowdsecurity/postfix und crowdsecurity/dovecot: Diese beiden Collections sind speziell für die Überwachung und den Schutz von Postfix- und Dovecot-Mailservern.
- crowdsecurity/nginx: Eine Collection, die speziell für die Überwachung und den Schutz von Nginx-Webservern entwickelt wurde.

Diese Umgebungsvariablen sind entscheidend für die Konfiguration von CrowdSec. Sie ermöglichen es, das Verhalten von CrowdSec fein abzustimmen und an die spezifischen Anforderungen deines Systems anzupassen. Es ist wichtig, diese Werte sorgfältig zu überprüfen und zu aktualisieren, um die bestmögliche Sicherheit zu gewährleisten.

## Konfiguration der acquis.yaml

Um die Konfigurationsdateien von CrowdSec zu generieren, müssen wir den CrowdSec-Dienst kurz starten. Dazu wechseln wir zunächst in das Verzeichnis unserer Docker-Compose-Datei für den Traefik-CrowdSec-Stack und starten dann den Dienst:

```
    # cd /opt/containers/traefik-crowdsec-stack
    docker compose up crowdsec -d && docker compose down
```

Mit dem Befehl docker compose up crowdsec -d starten wir den CrowdSec-Dienst im Hintergrundmodus. Schließlich beenden wir den Dienst wieder mit docker compose down.

Jetzt sollten alle Konfigurationsdateien von CrowdSec vorhanden sein und wir können nun die acquis.yaml-Datei anpassen. In der acquis.yaml-Datei werden die Log-Dateien definiert welche eingelesen und beobachtet werden sollen. Hier ist es wichtig, dass die Logdateien und Services auch in CrowdSec eingebunden sind. Dies habe ich in dieser Anleitung bereits in der docker-compose.yml angelegt:

```
    version: "3.9"
    services:
    crowdsec:
        ...
        volumes:
        ...
        # Hier wird die auth.log vom System in CrowdSec eingebracht
        - /var/log/auth.log:/var/log/auth.log:ro
        # Hier wird die der Ordner in den Traefik seine Logs schreibt in CrowdSec eingebracht
        - /var/log/traefik:/var/log/traefik:ro
        ...
    traefik:
        ...
        volumes:
        ...
        # Hier wird der Ordner in den Traefik seine Logs schreibt auf den Host gemounted
        - /var/log/traefik/:/var/log/traefik/
        ...
    ...
...
```

Nun zur acquis.yaml-Datei. Die haben wir nun generiert. Nach aktuellem Stand sieht diese so aus:

```
    filenames:
    - /var/log/nginx/*.log
    - ./tests/nginx/nginx.log
    #this is not a syslog log, indicate which kind of logs it is
    labels:
    type: nginx
    ---
    filenames:
    - /var/log/auth.log
    - /var/log/syslog
    labels:
    type: syslog
    ---
    filename: /var/log/apache2/*.log
    labels:
    type: apache2
```

Wir passen diese nun an unsere Bedürfnisse an und fügen folgendes ein bzw. ersetzen den vorhandenen Inhalt.

```
filenames:
 - /var/log/auth.log
 - /var/log/syslog
labels:
  type: syslog
---
filenames:
  - /var/log/traefik/*.log
labels:
  type: traefik
---
```

Im ersten Abschnitt der Konfigurationsdatei werden die auth.log und syslog Dateien zur Analyse hinzugefügt. Das Label “syslog” wird diesen Dateien zugeordnet. Dies ermöglicht es CrowdSec, bestimmte Analysemethoden auf diese Dateien anzuwenden, die für syslog-Logs geeignet sind.

Im zweiten Abschnitt der Konfigurationsdatei fügen wir alle Logdateien hinzu, die im Verzeichnis /var/log/traefik/ liegen und deren Dateinamen mit .log enden. Diesen Dateien weisen wir das Label “traefik” zu. So kann CrowdSec spezifische Analysemethoden anwenden, die für Traefik-Logs geeignet sind.

## Traefik und Crowdsec verheiraten – der Bouncer

CrowdSec hat nun die Fähigkeit, Logdateien zu analysieren und verdächtige IP-Adressen in eine Sperrliste aufzunehmen – das ist ein großer Schritt! Doch in der aktuellen Konfiguration haben wir noch keine Maßnahmen ergriffen, um potenzielle Angriffe tatsächlich abzuwehren. Das ist die Aufgabe sogenannter “Bouncer” in CrowdSec.

Es gibt eine Vielzahl an verschiedenen Bouncern für diverse Einsatzgebiete: Es gibt zum Beispiel Bouncer für Firewalls wie iptables oder nftables, und es gibt auch Bouncer zur Steuerung der Firewall von Cloudflare. Für unseren konkreten Anwendungsfall ist jedoch der Traefik Bouncer besonders interessant, da er die Fähigkeit hat, speziell mit unserem Traefik Load Balancer zu interagieren.

## Traefik CrowdSec Bouncer

### Access Token anlegen

In der config/traefik-crowdsec-bouncer.env haben wir die Variable CROWDSEC_BOUNCER_API_KEY angelegt und um diese mit einem Access-Token bzw. API-Key auch nutzen zu können müssen wir diesen wie folgt generieren:

```
# cd /opt/containers/traefik-crowdsec-stack
docker compose up crowdsec -d
docker compose exec -t crowdsec cscli bouncers add traefik-crowdsec-bouncer
docker compose down
```

So, oder so ähnlich sollte die Ausgabe aussehen:

```
Api key for 'traefik-crowdsec-bouncer':

   ee21c448d67e04550dec5b07b42ad6ee

Please keep this key since you will not be able to retrieve it!
```

Nun speichern wir uns den generierten Schlüssel (in diesem Beispiel: ee21c448d67e04550dec5b07b42ad6ee) in die Zwischenablage und fügen ihn in unsere config/traefik-crowdsec-bouncer.env ein.

### Traefik kontrollieren

Wie wir bereits in einem früheren Abschnitt dieser Anleitung festgelegt haben, wird in der dynamic_conf.yml-Datei die traefik-crowdsec-bouncer-Konfiguration definiert:

```
traefik-crowdsec-bouncer:
  forwardauth:
    address: http://traefik-crowdsec-bouncer:8080/api/v1/forwardAuth
    trustForwardHeader: true
```

Dieser Abschnitt ermöglicht es Traefik, mit dem CrowdSec Bouncer zu kommunizieren. Hierbei müssen wir sicherstellen, dass der unter address angegebene Hostname dem entspricht, den wir in der .env-Datei unter folgendem Punkt definiert haben:

```
TRAEFIK_CROWDSEC_BOUNCER_HOSTNAME=traefik-crowdsec-bouncer
```

definiert ist, verwendet werden.

In der traefik.yml-Datei haben wir unter entryPoints Traefik angewiesen, bei jeder Anfrage, die über den jeweiligen Point web bzw. websecure kommt, diese direkt über die Middleware an den Bouncer zu senden:

```
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: "websecure"
          scheme: "https"
      middlewares:
        - traefik-crowdsec-bouncer@file
  websecure:
    address: ":443"
    http:
      middlewares:
        - traefik-crowdsec-bouncer@file
```

Diese Konfiguration gewährleistet letztendlich das erfolgreiche Zusammenspiel zwischen allen Komponenten. Traefik kommuniziert mit dem Bouncer, der wiederum mit CrowdSec kommuniziert. Diese strukturierte Kommunikation zwischen den Komponenten sorgt dafür, dass potenziell schädliche Anfragen effektiv blockiert werden.

## Dienst starten

Uff! Das war wirklich eine lange und gründliche Anleitung bis jetzt. Ich habe mein Bestes gegeben, um viele Aspekte direkt zu erläutern und das Verständnis der Funktionsweise sowie des Aufbaus des Stacks zu erleichtern.

Jetzt, bevor wir mit dem Starten des Dienstes fortfahren, möchte ich dich bitten: Nimm dir einen Moment Zeit, geh nochmal alle Schritte durch und prüfe, ob alle Dateien richtig erstellt und mit dem passenden Inhalt gefüllt wurden.

Also, gönn dir eine kleine Pause, streck dich mal und gönn deinen Augen eine kurze Verschnaufpause vom Bildschirm. Dann, mit frischem Blick und voller Energie, können wir uns dem nächsten Schritt zuwenden. Und keine Sorge, wir sind schon fast am Ziel!

☕️☕️☕️

Bereit?

```
# cd /opt/containers/traefik-crowdsec-stack
docker compose up -d
```

🚀🚀🚀 Fertig, oder?

Wir könnten noch einige optionale Dinge hinzufügen. Es handelt sich dabei um Extras, die nicht unbedingt notwendig sind, aber je nach deinen spezifischen Anforderungen nützlich sein könnten. Bleib also dran und lass uns diese letzten Schritte gemeinsam erledigen!

## Überprüfung

Natürlich sollten wir zwischendurch und gemäß dieser Anleitung immer wieder überprüfen, ob alles funktioniert, wie es sollte. Das tun wir jetzt nach all diesen Schritten.

Wir haben den Container ja bereits gestartet. Als erstes überprüfen wir, ob alle Container als “healthy” (gesund) markiert sind:

```
# cd /opt/containers/traefik-crowdsec-stack
docker compose ps
```

```
root@mail:/opt/containers/traefik-crowdsec-stack# docker compose ps
NAME                       IMAGE                                       COMMAND                  SERVICE                    CREATED             STATUS                  PORTS
crowdsec                   crowdsecurity/crowdsec:latest               "/bin/sh -c '/bin/ba…"   crowdsec                   3 days ago          Up 19 hours (healthy)
traefik                    traefik:2.10                                "/entrypoint.sh trae…"   traefik                    3 days ago          Up 22 hours (healthy)   0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp
traefik_crowdsec_bouncer   fbonalair/traefik-crowdsec-bouncer:latest   "/app"                   traefik_crowdsec_bouncer   3 days ago          Up 3 days (healthy)
root@mail:/opt/containers/traefik-crowdsec-stack#
```

Wenn wir alles richtig gemacht haben, sind alle Container als “healthy” markiert.

Dann rufen wir das Traefik-Dashboard mit der zuvor festgelegten URL auf. Das Dashboard sollte sich öffnen und auch ein valides LE-Zertifikat haben.

Beim Öffnen des Dashboards werden auch Logdateien erstellt, und diese überprüfen wir als nächstes:

```
cd /var/log/traefik
ls -all
cat traefik.log
cat access.log
```

Hier sollten wir idealerweise die Dateien traefik.log und access.log finden, und in beide sollte etwas geschrieben sein. Wenn die Datei access.log nicht vorhanden ist, ist das kein Beinbruch, sollte aber beobachtet werden.

Wenn das alles passt, betrachten wir mit dem Befehl:

```
docker exec crowdsec cscli metrics
```

die ganz oben stehenden Acquisition Metrics. Dort sollte nun die traefik.log aufgeführt sein. Wenn die Datei access.log im System vorhanden ist, sollte sie ebenfalls dort erscheinen.

## Optional

Es gibt noch einige optionale Punkte. Diesen Bereich werde ich nach und nach erweitern bzw. auf vorhandene Anleitungen verweisen!
9.1. CrowdSec aktuell halten

Die benutzten COLLECTIONS werden überwiegend durch die Community gepflegt und natürlich auch auf neue Crowdsec-Versionen angepasst. Damit wir nicht in einen Fehler laufen oder eine veraltet COLLECTION verwenden ist es Sinnvoll diese regelmäßig zu aktualisieren. Dazu legen wir uns einen Cronjob an:

```
crontab -e
```

Dieser Cronjob wird jeden Tag um 03:00 Uhr aufgerufen, aktualisiert die Pakete aus dem CrowdSec Hub und läd die Konfiguration neu.

```
0 3 * * * docker exec crowdsec cscli hub update && docker exec crowdsec cscli hub upgrade && docker exec -t crowdsec kill -SIGHUP 1 >/dev/null 2>&1
```

### Traefik Dashboard schützen

Um das Traefik Dashboard abzusichern und unbefugten Zugriff zu verhindern, wird empfohlen, eine zusätzliche Authentifizierung einzurichten. Dadurch wird eine Benutzername-Passwort-Überprüfung erforderlich, um auf das Dashboard zugreifen zu können.

Traefik bietet eine einfache Methode zur Implementierung der Authentifizierung. Um dies zu erreichen, müssen wir zunächst die folgenden Pakete auf unserem System installieren:

```
sudo apt update && apt install apache2-utils
```

Nachdem wir diese Schritte durchgeführt haben, müssen wir innerhalb von Traefik eine Middleware konfigurieren. Bevor wir dies tun, erstellen wir ein Passwort mit dem folgenden Befehl:

```
echo $(htpasswd -nb DeinUsername 'DeinSuperSicheresPasswort')

# Ausgabe
DeinUsername:$apr1$xSRxT4UY$wk42WRgVzBW5Pf69sS5aT.
```

Es wird empfohlen, die Ausgabe zu speichern, zum Beispiel durch Kopieren und Einfügen in eine Textdatei.

### dynamic_conf.yml anpassen

Jetzt ist es an der Zeit, die Middleware zu konfigurieren. Dazu öffnen wir die Datei dynamic_conf.yml mit Texteditor.
Wir befinden uns im Abschnitt “http” -> “middlewares”.
Hier fügen wir nun die Konfiguration für unsere Schutzmaßnahmen hinzu:

```
traefikAuth:
  basicAuth:
  users:
    - "DeinUsername:$apr1$xSRxT4UY$wk42WRgVzBW5Pf69sS5aT."
```

Hierbei ersetzen wir natürlich “DeinUsername” und “$apr1$xSRxT4UY$wk42WRgVzBW5Pf69sS5aT.” durch die zuvor generierten Werte.

Dieses Snippet fügen wir an beliebiger Stelle in die middlewares ein:

```
...
http:
  middlewares:
    default:
      chain:
        middlewares:
          - default-security-headers
          - gzip

    default-security-headers:
      headers:
        browserXssFilter: true
        contentTypeNosniff: true
        forceSTSHeader: true
        frameDeny: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
        customFrameOptionsValue: "SAMEORIGIN"

    gzip:
      compress: {}

    traefik-crowdsec-bouncer:
      forwardauth:
        address: http://traefik-crowdsec-bouncer:8080/api/v1/forwardAuth
        trustForwardHeader: true

    real-ip-cf:
      plugin:
        real-ip:
          Proxy:
            - proxyHeadername: "*"
              realIP: Cf-Connecting-Ip
              OverwriteXFF: true

    traefikAuth:
      basicAuth:
        users:
          - "DeinUsername:$apr1$xSRxT4UY$wk42WRgVzBW5Pf69sS5aT."
...
```

### docker-compose.yml anpassen

Im letzten Schritt müssen wir Anpassungen in der Datei docker-compose.yml vornehmen. Öffnen Sie die Datei mit einem Texteditor.

```
traefik:
  container_name: ${TRAEFIK_CONTAINER_NAME:-traefik}
  depends_on:
    crowdsec:
      condition: service_healthy
  env_file: ./config/traefik.env
  hostname: ${TRAEFIK_HOSTNAME:-traefik}
  healthcheck:
    test: ["CMD", "traefik", "healthcheck", "--ping"]
    interval: 10s
    timeout: 1s
    retries: 3
    start_period: 10s
  image: ${TRAEFIK_IMAGE:-traefik}:${TRAEFIK_IMAGE_VERSION:-2.10}
  labels:
    traefik.docker.network: proxy
    traefik.enable: "true"
    traefik.http.routers.traefik.entrypoints: websecure
    traefik.http.routers.traefik.middlewares: default@file
    traefik.http.routers.traefik.rule: Host(${TRAEFIK_LABELS_TRAEFIK_HOST})
    traefik.http.routers.traefik.service: api@internal
    traefik.http.routers.traefik.tls: "true"
    traefik.http.routers.traefik.tls.certresolver: http_resolver
    traefik.http.services.traefik.loadbalancer.sticky.cookie.httpOnly: "true"
    traefik.http.services.traefik.loadbalancer.sticky.cookie.secure: "true"
    traefik.http.routers.pingweb.rule: PathPrefix(`/ping`)
    traefik.http.routers.pingweb.service: ping@internal
    traefik.http.routers.pingweb.entrypoints: websecure
  networks:
    crowdsec:
      ipv4_address: ${TRAEFIK_NETWORKS_CROWDSEC_IPV4:-172.31.254.253}
    proxy:
      ipv4_address: ${TRAEFIK_NETWORKS_PROXY_IPV4:-172.16.255.254}
  ports:
    - "80:80"
    - "443:443"
  restart: unless-stopped
  security_opt:
    - no-new-privileges:true
  volumes:
    - /etc/localtime:/etc/localtime:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - /var/log/traefik/:/var/log/traefik/
    - ./traefik/traefik.yml:/traefik.yml:ro
    - ./traefik/acme_letsencrypt.json:/acme_letsencrypt.json
    - ./traefik/tls_letsencrypt.json:/tls_letsencrypt.json
    - ./traefik/dynamic_conf.yml:/dynamic_conf.yml
```

Innerhalb dieses Abschnitts finden Sie unter “labels” das Label:

```
traefik.http.routers.traefik.middlewares: default@file
```

Erweitern Sie diese Zeile nun um unsere gerade erstellte Middleware “traefikAuth”:

```
traefik.http.routers.traefik.middlewares: default@file,traefikAuth@file
```

### Neustart des Setups

Abschließend führen wir einen Neustart des FullStacks durch und überprüfen anschließend, ob beim Aufruf des Traefik Dashboards nun ein Passwort abgefragt wird.

Wechseln Sie zum Verzeichnis des Traefik-Crowdsec-Stacks:

```
cd /opt/containers/traefik-crowdsec-stack
```

Starten Sie den FullStack neu und erzwingen Sie die Neuerstellung der Container:

```
docker compose up -d --force-recreate
```

Nachdem der Neustart abgeschlossen ist, überprüfen Sie, ob beim Aufruf des Traefik Dashboards nun ein Passwort abgefragt wird.
