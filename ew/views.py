from django.shortcuts import render
from django.http import HttpResponse
import json
import oracledb
import cise_oracle_info


def oracledb_conn():
    conn = oracledb.connect(
        user=cise_oracle_info.user,
        password=cise_oracle_info.password,
        host=cise_oracle_info.host,
        port=cise_oracle_info.port,
        sid=cise_oracle_info.sid
    )
    return conn


# Create your views here.
def my_view(request):
    conn = oracledb_conn()
    cursor = conn.cursor()
    context = {}

    selected_fips = 'NONE'
    if request.method == "POST" and ("onefips" in request.POST.keys()):
        for key, val in request.POST.items():
            print(key, val)
        selected_fips = request.POST['selectfips']
        tornado = 'NONE'
        hail = 'NONE'
        wind = 'NONE'

        if "Tornado" in request.POST.keys():
            tornado = 'TORN'
        if "Wind" in request.POST.keys():
            wind = "WIND"
        if "Hail" in request.POST.keys():
            hail = "HAIL"
        query_items = (selected_fips, tornado, hail, wind)
        print(query_items, request.POST['btnradio'])

        if request.POST['btnradio'] == 'pop':
            select_query = """
                WITH target AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM events) yr LEFT JOIN 
                    events e
                    ON EXTRACT(YEAR FROM e.event_date)=yr.year AND location_id=(:1) AND event_type IN (:2, :3, :4)
                    GROUP BY yr.year, location_id)
                SELECT t.year, p.population, t.num
                FROM populations p, target t
                WHERE p.year=t.year AND p.location_id IN 
                    (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
                ORDER BY year"""
        elif request.POST['btnradio'] == 'hpi':
            print("HERE")
            select_query = """
                WITH target AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM events) yr
                    LEFT JOIN events e
                    ON EXTRACT(YEAR FROM e.event_date)=yr.year AND location_id=(:1) AND event_type IN (:2, :3, :4)
                    GROUP BY yr.year, location_id)
                SELECT t.year, h.hpi, t.num
                FROM housing_prices h, target t
                WHERE h.year=t.year AND h.location_id IN 
                    (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
                ORDER BY year"""
        else:
            select_query = """
                WITH allyears AS (
                    SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM events),
                allevents AS (
                    SELECT allyears.year, event_type
                    FROM allyears LEFT JOIN events e
                        ON EXTRACT(YEAR FROM e.event_date)=allyears.year
                        AND location_id=(:1)),
                events1 AS (
                    SELECT allyears.year, COUNT(event_type) AS tornado
                    FROM allyears LEFT JOIN allevents e
                        ON e.year=allyears.year AND event_type=(:2)
                    GROUP BY  allyears.year
                    ),
                events2 AS (
                    SELECT allyears.year, COUNT(event_type) AS wind
                    FROM allyears LEFT JOIN allevents e
                        ON e.year=allyears.year AND event_type=(:3)
                    GROUP BY  allyears.year
                    ),
                events3 AS (
                    SELECT allyears.year, COUNT(event_type) AS hail
                    FROM allyears LEFT JOIN allevents e
                        ON e.year=allyears.year AND event_type=(:4)
                    GROUP BY  allyears.year)
                SELECT * FROM events1 NATURAL JOIN events2 NATURAL JOIN events3 ORDER BY year"""
        res = cursor.execute(select_query, query_items)

        the_chart = {
            "ioi": request.POST['btnradio'],
            "events": query_items[1:],
            "fips_ct": 1,
            "yr": [],
            "d1": [],
            "d2": [],
            "d3": ["Empty"],
        }

        for i in res:
            the_chart["yr"].append(i[0])
            the_chart["d1"].append(i[1])
            the_chart["d2"].append(i[2])
            if len(i) > 3:
                the_chart["d3"].append(i[3])
        print(the_chart)
        context['the_chart'] = the_chart
        pass
    elif request.method == "POST" and ("twofips" in request.POST.keys()):
        select_query = """
            WITH allevents AS (
                SELECT EXTRACT(MONTH FROM event_date) AS mon, EXTRACT(YEAR FROM event_date) AS yr, location_id, event_type
                FROM events
                WHERE location_id=1027 OR location_id=41053),
            e1 AS (
                SELECT mon, AVG(num1) AS avg1 FROM (
                    SELECT yr, mon, COUNT(event_type) as num1
                    FROM allevents
                    WHERE location_id=1027
                    GROUP BY yr, mon)
                GROUP BY mon),
            e2 AS (
                SELECT mon, AVG(num2) AS avg2 FROM (
                    SELECT yr, mon, COUNT(event_type) as num2
                    FROM allevents
                    WHERE location_id=41053
                    GROUP BY yr, mon)
                GROUP BY mon),
            allmonths AS (
                SELECT DISTINCT EXTRACT(MONTH FROM event_date) AS mon FROM events)
            SELECT allmonths.mon AS mon, COALESCE(avg1, 0), COALESCE(avg2, 0)
            FROM (allmonths LEFT JOIN e1 ON  e1.mon=allmonths.mon) LEFT JOIN e2 ON allmonths.mon=e2.mon
            ORDER BY mon ASC
        """
        fips1 = request.POST['selectfips1']
        fips2 = request.POST['selectfips2']
        query_items = (fips1, fips1, fips2, fips2 )
        res = cursor.execute(select_query)#, query_items)
        the_chart = {
            "fips_ct": 2,
            "yr": [],
            "d1": [],
            "d2": [],
        }

        for i in res:
            the_chart["yr"].append(i[0])
            the_chart["d1"].append(i[1])
            the_chart["d2"].append(i[2])

        print(the_chart)
        context['the_chart'] = the_chart

        pass

    location_data = []
    all_res = cursor.execute("""SELECT fips, countyname, statename FROM location ORDER BY fips ASC""")
    for i in all_res:
        location_data.append([i[0], i[1], i[2]])
    context['location_data'] = location_data
    conn.close()
    return render(request, 'WebsiteDesign/MainPage.html', context=context)


# https://www.chartjs.org/docs/latest/getting-started/
# https://studygyaan.com/django/how-to-use-chart-js-in-django
# https://www.chartjs.org/docs/latest/samples/line/multi-axis.html multiple lines
# https://github.com/akjasim/cb_dj_dependent_dropdown for chained dropdowns maybe

# Could also make a new chart and script that are run when whatever {{ the_chart.d3 }} var exists.
# This would be a new chart and script instead of modifying the old one

def one_fips():
    return
