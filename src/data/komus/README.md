## Необходимые библиотеки

Для того чтобы запустить скрипт необходимы

```
undetected-chromedriver==3.5.5
selenium==4.27.1
```

А также нужен Chrome браузер последней версии.

## Запуск скрипта

Для запуска сбора данных необходимо в параметрах запуска указать ссылки на каталоги(Разделитель - пробел). 

Пример(из корня проекта):

```bash
.\src\data\komus\script.bat "https://www.komus.ru/katalog/podarki-i-suveniry/originalnye-podarki/antistressy/c/4951/" "https://www.komus.ru/katalog/podarki-i-suveniry/tovary-dlya-sporta-piknika-i-otdykha/tovary-dlya-plavaniya/c/4929/"
```

Результат работы:  
Подготовленные файлы каталогов в виде json.