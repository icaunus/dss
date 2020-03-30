from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, QueryDict
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

def rows2ObjectArray(rows, key):
  result = []
  
  for r in rows:
    r2o = {key:r[0]}
    result.append(r2o)
  
  return result

def continents(request):
  sql = 'SELECT DISTINCT continent FROM country ORDER BY continent;'
  rows = fetch(sql)
  r2j = rows2ObjectArray(rows, "continent")
  print("CONTINENTS/r2j: {}\n".format(r2j))
  return JsonResponse(r2j, safe=False)

def regions(request):
  continent = urllib.parse.unquote(request.GET['continent'])
  sql = "SELECT DISTINCT region FROM country WHERE continent = '" + continent + "' ORDER BY region;"
  rows = fetch(sql)
  r2j = rows2ObjectArray(rows, 'region')

  return JsonResponse(r2j, safe=False)

def countries(request):
  region = urllib.parse.unquote(request.GET['region'])
  sql = "SELECT name, code FROM country WHERE region = '" + region + "' ORDER BY name;"
  rows = fetch(sql)
  result = []
  
  for r in rows:
    r2o = {"country":r[0], "code":r[1]}
    result.append(r2o)

  return JsonResponse(result, safe=False)

def country(request):
  countryName = request.GET['name']
  sql = "SELECT * FROM country WHERE name = '{}';".format(countryName)
  rows = fetch(sql)
  result = []

  for r in rows:
    code, name, continent, region, surfaceArea, independence, population, lifeExpectancy, gnp, gnpOld, localName, governmentForm, headOfState, capital, code2 = r
    r2o = { "code": code, "name": name, "continent": continent, "region": region, "surfaceArea": surfaceArea, "independence": independence,
        "population": population, "lifeExpectancy": lifeExpectancy, "gnp": gnp, "gnpOld": gnpOld, "localName": localName, "governmentForm": governmentForm, 
        "headOfState": headOfState, "capital": capital, "code2": code2 
    }
    result.append(r2o)

  return JsonResponse(result, safe=False)

def cities(request):
  countryName = urllib.parse.unquote(request.GET['countryName'])
  sql = "SELECT name, countrycode FROM city WHERE countryCode = ( SELECT code FROM country WHERE name = '{}' ) ORDER BY name;".format(countryName)
  rows = fetch(sql)
  r2j = rows2ObjectArray(rows, 'city')

  return JsonResponse(r2j, safe=False)

def city(request):
  city = urllib.parse.unquote(request.GET['city'])
  countryCode = request.GET['countryCode']
  sql = "SELECT * FROM city WHERE id = (SELECT id FROM city WHERE name = '{}' and countrycode = '{}');".format(city, countryCode)
  rows = fetch(sql)
  result = []

  for r in rows:
    cityId, name, countryCode, district, population = r
    r2o = {"id": cityId, "name": name, "countryCode": countryCode, "district": district, "population": population}
    result.append(r2o)

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
  sql = ''
  r2j = {}
  '''
  try:
    newId = nextId(cn, tableName)
    name = request.POST['newCity']
    country = request.POST['newCountryCode']
    district = request.POST['district']
    population = request.POST['population']
    sql = "INSERT INTO city (id, name, countrycode, district, population) VALUES ({}, '{}', '{}', '{}', {});".format(newId, name, country, district, population)
    r2j = change(cn, sql)
  except KeyError as ke:
    print('add/key error: {}'.format(str(ke)))
  '''
  newId = nextId(cn, tableName)
  name = request.POST.get('newCity', False) # POST['newCity']
  country = request.POST.get('newCountryCode', False) # ['newCountryCode']
  district = request.POST.get('district', False) # ['district']
  population = request.POST.get('population', 0) # ['population']
  sql = "INSERT INTO city (id, name, countrycode, district, population) VALUES ({}, '{}', '{}', '{}', '{}');".format(newId, name, country, district, population)
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
def delete(request, cityId):
  # body = QueryDict(request)
  # cityId = body.get('cityId')  # request.DELETE.get('cityId')
  cn = connect()
  sql = "DELETE FROM city WHERE id = {};".format(cityId)
  print("DELETE: {}\n".format(sql))
  r2j = change(cn, sql)

  return JsonResponse(r2j, safe=False)
