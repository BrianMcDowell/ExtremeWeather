from django.shortcuts import render
import oracledb
import json
import cise_oracle_info


def oracledb_conn():
    conn = oracledb.connect(
        user=cise_oracle_info.user,
        password=cise_oracle_info.password,
        host=cise_oracle_info.host,
        port=cise_oracle_info.port,
        sid=cise_oracle_info.sid,
    )
    return conn


# Create your views here.
def my_view(request):
    # Write SQL queries to show how many rows are present in database
    conn = oracledb_conn()
    cursor = conn.cursor()
    context = {}
    if request.method == "POST":
        tuple_count_query = """
        SELECT l.lnum + p.pnum + h.hnum + e.enum
        FROM (SELECT COUNT(*) AS lnum FROM michaelrodelo.location) l,
            (SELECT COUNT(*) AS pnum FROM michaelrodelo.populations) p,
            (SELECT COUNT(*) AS hnum FROM michaelrodelo.housing_prices) h,
            (SELECT COUNT(*) AS enum FROM michaelrodelo.events) e
        """
        res = cursor.execute(tuple_count_query).fetchone()[0]
        context["tuple_count_res"] = res
    conn.close()
    return render(request, 'WebsiteDesign/MainPage.html', context=context)


def results(request):
    context = {}
    conn = oracledb_conn()
    cursor = conn.cursor()
    the_chart = {
        "yr": [],
        "data1": [],
        "data2": [],
        "data3": [],
    }
    context["d3hide"] = 1
    fips = "None"
    if request.method == "POST":
        """ Obtain query items from request.POST """
        for key, val in request.POST.items():
            print(key, val)

        tornado = "NONE"
        hail = "NONE"
        wind = "NONE"
        fips = request.POST["fips"]
        #context["fips"] = fips
        wx_ioi = []
        if "Tornado" in request.POST.keys():
            tornado = "TORN"
            wx_ioi.append("Tornadoes")
        if "Hail" in request.POST.keys():
            hail = "HAIL"
            wx_ioi.append("Hail")
        if "Wind" in request.POST.keys():
            wind = "WIND"
            wx_ioi.append("Wind")
        query_items = (fips, tornado, hail, wind)
        ioi = request.POST["btnradio"]
        wx_vs_wx = False
        if ioi == "pop":
            select_query = """
                WITH target AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM michaelrodelo.events) yr LEFT JOIN 
                    michaelrodelo.events e
                    ON EXTRACT(YEAR FROM e.event_date)=yr.year
                        AND location_id=(:1)
                        AND event_type IN (:2, :3, :4)
                    GROUP BY yr.year, location_id)
                SELECT t.year, p.population, t.num
                FROM michaelrodelo.populations p, target t
                WHERE p.year=t.year AND p.location_id IN 
                    (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
                ORDER BY year
            """
            context["ioi"] = json.dumps("Population")
        elif ioi == "hpi":
            select_query = """
                WITH target AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM michaelrodelo.events) yr LEFT JOIN 
                    michaelrodelo.events e
                    ON EXTRACT(YEAR FROM e.event_date)=yr.year
                        AND location_id=(:1)
                        AND event_type IN (:2, :3, :4)
                    GROUP BY yr.year, location_id)
                SELECT t.year, h.hpi, t.num
                FROM michaelrodelo.housing_prices h, target t
                WHERE h.year=t.year AND h.location_id IN 
                    (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
                ORDER BY year
            """
            context["ioi"] = json.dumps("Housing Price Index")
        else:
            select_query = """
                WITH allyears AS (
                    SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM michaelrodelo.events),
                allevents AS (
                    SELECT allyears.year, event_type
                    FROM allyears LEFT JOIN michaelrodelo.events e
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
                SELECT * FROM events1 NATURAL JOIN events2 NATURAL JOIN events3 ORDER BY year
            """
            wx_vs_wx = True
            context["ioi"] = json.dumps("Tornado")
        res = cursor.execute(select_query, query_items)


        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
            if len(item) > 3:
                the_chart["data3"].append(item[3])
                context["d3hide"] = 0
        context["the_chart"] = the_chart

        context["wx_ioi"] = json.dumps(", ".join(wx_ioi))
    context["fips"] = fips
    location_data = []
    location_res = cursor.execute(
        """
        SELECT fips, countyname, statename
        FROM michaelrodelo.location
        ORDER BY fips ASC
        """
    )
    for location in location_res:
        location_data.append([location[0], location[1], location[2]])
    context["location_data"] = location_data
    conn.close()
    return render(request, 'WebsiteDesign/Results.html', context=context)

def twofips(request):
    # Need to change html to work with two FIPS codes
    context = {}
    conn = oracledb_conn()
    cursor = conn.cursor()
    the_chart = {
        "yr": [],
        "data1": [],
        "data2": [],
    }
    fips1 = "None"
    fips2 = "None"
    if request.method == "POST":
        for key, val in request.POST.items():
            print(key, val)
        tornado = "NONE"
        hail = "NONE"
        wind = "NONE"
        fips1 = int(request.POST["fips1"])
        fips2 = int(request.POST["fips2"])
        the_chart["d1fips"] = json.dumps(fips1)
        the_chart["d2fips"] = json.dumps(fips2)
        wx_ioi = []
        if "Tornado" in request.POST.keys():
            tornado = "TORN"
            wx_ioi.append("Tornadoes")
        if "Hail" in request.POST.keys():
            hail = "HAIL"
            wx_ioi.append("Hail")
        if "Wind" in request.POST.keys():
            wind = "WIND"
            wx_ioi.append("Wind")
        month_or_year = request.POST["btnradio"]
        if month_or_year == "month":
            query_items = (fips1, fips2, fips1, fips2)
            select_query = """
                WITH allevents AS (
                    SELECT EXTRACT(MONTH FROM event_date) AS mon, EXTRACT(YEAR FROM event_date) AS yr, location_id, event_type
                    FROM michaelrodelo.events
                    WHERE location_id=(:1) OR location_id=(:2)),
                e1 AS (
                    SELECT mon, AVG(num1) AS avg1 FROM (
                        SELECT yr, mon, COUNT(event_type) as num1
                        FROM allevents
                        WHERE location_id=(:3)
                        GROUP BY yr, mon)
                    GROUP BY mon),
                e2 AS (
                    SELECT mon, AVG(num2) AS avg2 FROM (
                        SELECT yr, mon, COUNT(event_type) as num2
                        FROM allevents
                        WHERE location_id=(:4)
                        GROUP BY yr, mon)
                    GROUP BY mon),
                allmonths AS (
                    SELECT DISTINCT EXTRACT(MONTH FROM event_date) AS mon FROM events)
                SELECT allmonths.mon AS mon, COALESCE(avg1, 0), COALESCE(avg2, 0)
                FROM (allmonths LEFT JOIN e1 ON  e1.mon=allmonths.mon) LEFT JOIN e2 ON allmonths.mon=e2.mon
                ORDER BY mon ASC
            """
        else:
            query_items = (fips1, fips1, fips2, fips2)
            select_query = """
                WITH allyears AS (
                    SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM michaelrodelo.events),
                t1 AS (
                    SELECT allyears.year, COALESCE(location_id, (:1)) AS loc1, count(event_type) AS num1
                    FROM allyears LEFT JOIN michaelrodelo.events e 
                        ON EXTRACT(YEAR FROM e.event_date)=allyears.year AND location_id=(:2)
                    GROUP BY allyears.year, location_id),
                t2 AS (
                    SELECT allyears.year, COALESCE(location_id, (:3)) AS loc2, count(event_type) AS num2
                    FROM allyears LEFT JOIN michaelrodelo.events e
                        ON EXTRACT(YEAR FROM e.event_date)=allyears.year AND location_id=(:4)
                    GROUP BY allyears.year, location_id)
                SELECT year, num1, num2 FROM t1 NATURAL JOIN t2 ORDER BY year ASC
            """
        res = cursor.execute(select_query, query_items)
        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
            if len(item) > 3:
                the_chart["data3"].append(item[3])
                context["d3hide"] = 0
        context["the_chart"] = the_chart
    location_data = []
    location_res = cursor.execute(
        """
        SELECT fips, countyname, statename
        FROM michaelrodelo.location
        ORDER BY fips ASC
        """
    )
    for location in location_res:
        location_data.append([location[0], location[1], location[2]])
    context["location_data"] = location_data
    conn.close()
    return render(request, 'WebsiteDesign/TwoFipsResults.html', context=context)

def states(request):
    # borrowed from twofips
    context = {}
    conn = oracledb_conn()
    cursor = conn.cursor()
    the_chart = {
        "yr": [],
        "data1": [],
        "data2": [],
    }
    state1 = "None"
    state2 = "None"
    if request.method == "POST":
        for key, val in request.POST.items():
            print(key, val)
        state1 = request.POST["state1"]
        state2 = request.POST["state2"]
        the_chart["d1state"] = json.dumps(state1)
        the_chart["d2state"] = json.dumps(state2)

        query_items = (state1, 'NH')
        select_query = """
            SELECT p.year, total_population, total_events
            FROM
                (SELECT sum(p.population) as total_population, l.statename, p.year
                FROM michaelrodelo.populations p
                INNER JOIN michaelrodelo.location l 
                ON p.location_id = l.fips
                WHERE statename = (:1)      
                GROUP BY l.statename, p.year) p
            INNER JOIN
                (SELECT statename, year, sum(num) AS total_events
                FROM michaelrodelo.location l 
                    INNER JOIN 
                    (SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year 
                        FROM michaelrodelo.events) yr 
                    LEFT JOIN michaelrodelo.events e
                    ON EXTRACT(YEAR FROM e.event_date)=yr.year
                    GROUP BY yr.year, location_id) e
                ON l.fips = e.location_id
                WHERE statename = (:1)      
                GROUP BY statename, year) e
            ON p.year = e.year
            ORDER BY year ASC    
        """
        res = cursor.execute(select_query, query_items)
        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
            if len(item) > 3:
                the_chart["data3"].append(item[3])
                context["d3hide"] = 0
        context["the_chart"] = the_chart
    location_data = []
    location_res = cursor.execute(
        """
        SELECT DISTINCT statename
        FROM michaelrodelo.location
        ORDER BY statename ASC
        """
    )
    for location in location_res:
        location_data.append([location[0]])
    context["location_data"] = location_data
    conn.close()
    return render(request, 'WebsiteDesign/StatesResults.html', context=context)
