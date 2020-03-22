from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import psycopg2 as db
import urllib.parse

def connect():
  c = db.connect(
    host = 'localhost',
    port = '5432',
    user = 'world',
    password = 'world',
    database = 'world'
  )

  return c

def appidx(request):
  return HttpResponse('App index')

def fetch(sql):
  rows = ()

  try:
    cn = connect()
    cr = cn.cursor()
    cr.execute(sql)
    rows = cr.fetchall()
  except (Exception, db.Error) as err:
    print('DB error: ', err)
  finally:
    if cn:
      cr.close()
      cn.close()

  return rows

def nextId(connection, tableName):
  sql = 'SELECT MAX(id) FROM ' + tableName + ';'
  rowCount = -1

  try:
    cr = connection.cursor()
    cr.execute(sql)
    result = cr.fetchone()
    rowCount = result[0]
    rowCount += 1
  except (Exception, db.Error()) as err:
    print('DB error: ', err)
  finally:
    cr.close()

  return rowCount

def rows2Json(rows, key):
  result = []

  for r in rows:
    r2j = {key: r[0]}
    result.append(r2j)

  return result

def continents(request):
  sql = 'SELECT DISTINCT continent FROM country ORDER BY continent;'
  rows = fetch(sql)
  r2j = rows2Json(rows, 'continent')

  return JsonResponse(r2j, safe=False)

def regions(request):
  continent = urllib.parse.unquote(request.GET['continent'])
  sql = "SELECT DISTINCT region FROM country WHERE continent = '" + continent + "' ORDER BY region;"
  rows = fetch(sql)
  r2j = rows2Json(rows, 'region')

  return JsonResponse(r2j, safe=False)

def countries(request):
  region = urllib.parse.unquote(request.GET['region'])
  sql = "SELECT DISTINCT name FROM country WHERE region = '" + region + "' ORDER BY name;"
  rows = fetch(sql)
  r2j = rows2Json(rows, 'country')

  return JsonResponse(r2j, safe=False)

def country(request):
  countryName = request.GET['country']
  sql = "SELECT * FROM country WHERE name = '{}';".format(countryName)
  rows = fetch(sql)
  result = {}
    
  for r in rows:
    code, name, continent, region, surfaceArea, independence, population, lifeExpectancy, gnp, gnpOld, localName, governmentForm, headOfState, capital, code2 = r
    result = { "code": code, "name": name, "continent": continent, "region": region, "surfaceArea": surfaceArea, "independence": independence, "population": population,      "lifeExpectancy": lifeExpectancy, "gnp": gnp, "gnpOld": gnpOld, "localName": localName, "governmentForm": governmentForm, "headOfState": headOfState,
      "capital": capital, "code2": code2 }

  return JsonResponse(result, safe=False)

def cities(request):
  countryCode = urllib.parse.unquote(request.GET['countryCode'])
  sql = "SELECT name FROM city WHERE countrycode = '{}' ORDER BY name;".format(countryCode)
  rows = fetch(sql)
  r2j = rows2Json(rows, 'city')

  return JsonResponse(r2j, safe=False)

def city(request):
  city = urllib.parse.unquote(request.GET['city'])
  sql = "SELECT * FROM city WHERE id = (SELECT id FROM city WHERE name = '{}');".format(city)
  rows = fetch(sql)
  result = {}

  for r in rows:
    cityId, name, countryCode, district, population = r
    result = {"id": cityId, "name": name, "countryCode": countryCode, "district": district, "population": population}

  return JsonResponse(result, safe=False)

def change(cn, sql):
  try:
    cr = cn.cursor()
    cr.execute(sql)
    cn.commit()
    rowsAffected = cr.rowcount
  except (Exception, db.Error()) as err:
    print('DB error: ', err)
  finally:
    cr.close()
    cn.close()

  return {"rowsAffected": rowsAffected}

@csrf_exempt
def add(request):
  tableName = 'city'
  cn = connect()
  newId = nextId(cn, tableName)
  name = request.POST['city']
  country = request.POST['countryCode']
  district = request.POST['district']
  population = request.POST['population']
  sql = "INSERT INTO city (id, name, countrycode, district, population) VALUES ({}, '{}', '{}', '{}', {});".format(newId, name, country, district, population)

  r2j = change(cn, sql)
  return JsonResponse(r2j, safe=False)

@csrf_exempt
def update(request):
  count = 0
  sql = "UPDATE city SET "
  r2j = {}

  try:
    cityId = request.POST['id']
    name = request.POST['name']
    countryCode = request.POST['countryCode']
    district = request.POST['district']
    population = request.POST['population']
  except KeyError as ke:
    print('Request key error: ', ke)
  
  rqp = dict(request.POST)
  rqp2 = { k: v for k, v in rqp.items() if len(v[0]) > 0}
  del rqp2['id']

  for k, v in rqp2.items():
    if count == len(rqp2.items()) - 1:
      if type(v[0]) is str:
        sql += "{} = '{}' ".format(k, v[0])
      elif type(v[0]) is int:
        sql += "{} = {} ".format(k, v[0])  

      break
    elif count < len(rqp2.items()) - 1:
      if type(v[0]) is str:
        sql += "{} = '{}', ".format(k, v[0])
      elif type(v[0]) is int:
        sql += "{} = {}, ".format(k, v[0]) 

    count += 1
  
  sql += "WHERE id = {};".format(cityId)
  cn = connect()
  r2j = change(cn, sql)

  return JsonResponse(r2j, safe=False)

@csrf_exempt
def delete(request):
  cityName = request.POST['city']
  cn = connect()
  sql = "DELETE FROM city WHERE id = (SELECT id FROM city WHERE name = '{}');".format(cityName)
  r2j = change(cn, sql)

  return JsonResponse(r2j, safe=False)
