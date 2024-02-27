\*\*1- db yi ligfinder verileri ile ayaga kaldiralim
\*\*2- docker exec ile fastapi yapisinin temellerini atalim

docker build . -t ubuntu22-python310-base:latest : Done
docker run --name fastapi-cont -p 8083:8000 -it -e SHELL=/bin/bash -v /home/ortak/Desktop/HCU/LIG-3/lig-3-python-backend/src:/home/tosca ubuntu22-python310-base bash : Done

- kutuphane kurulumu yaptiktan sonra docker compose down yapinca kutuphane container icinden gidiyor. kutuphabne ekleyince --build ile ayaga kaldirmak gerekiyor
- docker commit ile son container dan image olsuturup surekli update kalabilyioruz
- login ve register endpointlerini yazalim >>> yazdik
- login ve register endpointlerini test edelim >>> yazdik
- connection pool ile db baglantilarini optimize edelim ve DB de ilk okumamizi yapalim > yaptik
- ligfinder ednpointleri ile test yapalim
- geo sqlalchemy ile db deki verileri cekelim. bakalim fonskiyonlarimiz calisiyor mu?|
  - sqlalchemy ile direk sql de kosturabiliyorz.
  - Hepsini geoslqlalchemy donusturcez diye bir sey yok. Olsa guzel olabilir
  - veri okumalari geoserver vb seyelr ile yapacaz. Ne kadarlik bir yuk olacak bilemiyoruz.
    8- black -l . ile git e push lamadan once kodlari standarta sokkma - https://stackoverflow.com/questions/71180810/python-black-code-formatter-is-there-any-way-to-apply-automatic-black-formatti

FUTURE TASK

- Auth modulunu gelistirme

  - /auth/register
  - /auth/login
  - auth/logout
  - auth/refresh-token
  - auth/forgot-password
  - auth/reset-password
  - auth/send-verification-email
  - auth/verify-email

- `logger = logging.getLogger(__name__) kullanimini ogren`
