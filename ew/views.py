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

def openOneFips(request):
    return render(request, 'WebsiteDesign/OneFips.html')

def openOneFips(request):
    return render(request, 'WebsiteDesign/TwoFipsResults.html')

def openStatesResults(request):
    return render(request, 'WebsiteDesign/StatesResults.html')


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
                WITH allyears AS (
                    SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year
                    FROM events),
                events_here AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS ct
                    FROM allyears yr 
                    LEFT JOIN events e ON
                        EXTRACT(YEAR FROM e.event_date)=yr.year
                        AND location_id=(:1)
                        AND event_type IN ((:2), (:3), (:4))
                    GROUP BY  yr.year, location_id)
                SELECT eh.year, p.population, eh.ct
                FROM populations p, events_here eh
                WHERE p.year=eh.year
                    AND p.location_id IN
                        (SELECT DISTINCT location_id
                        FROM events_here
                        WHERE location_id IS NOT NULL)
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


def onefips(request):
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
            context['torn'] = True
        if "Hail" in request.POST.keys():
            hail = "HAIL"
            wx_ioi.append("Hail")
            context['hail'] = True
        if "Wind" in request.POST.keys():
            wind = "WIND"
            wx_ioi.append("Wind")
            context['wind'] = True
        query_items = (fips, tornado, hail, wind)
        ioi = request.POST["btnradio"]
        wx_vs_wx = False
        if ioi == "pop":
            select_query = """
                WITH all_years AS (
                    SELECT year, location_id, population FROM michaelrodelo.populations WHERE location_id=:fips),
                delta_fips AS (
                    SELECT year, location_id, (((popa/popb) - 1) * 100) AS change
                    FROM (SELECT a.year, b.location_id, b.population AS popb, a.population AS popa
                        FROM all_years b INNER JOIN all_years a
                        ON b.year=a.year-1)),
                sum_all_years AS (
                    SELECT year, SUM(population) as sumpop
                    FROM michaelrodelo.populations
                    WHERE location_id IN 
                        (SELECT fips 
                        FROM michaelrodelo.location 
                        WHERE statename = 
                            (SELECT statename 
                            FROM michaelrodelo.location
                            WHERE fips=:fips))
                    GROUP BY year),
                delta_state AS (
                    SELECT year, (((popa/popb) - 1) * 100) AS change
                    FROM (SELECT a.year, b.sumpop AS popb, a.sumpop AS popa
                        FROM sum_all_years b INNER JOIN sum_all_years a
                        ON b.year=a.year-1)),
                combined_pop AS (
                    SELECT delta_fips.year, delta_fips.location_id, delta_fips.change AS delta_fips, delta_state.change AS delta_state
                    FROM delta_fips, delta_state
                    WHERE delta_state.year=delta_fips.year
                    ORDER BY year ASC),
                target AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM michaelrodelo.events) yr
                    LEFT JOIN michaelrodelo.events e ON
                        EXTRACT(YEAR FROM e.event_date)=yr.year
                        AND location_id=:fips AND event_type IN (:torn, :hail, :wind)
                    GROUP BY yr.year, location_id)
                SELECT t.year, ROUND(p.delta_fips, 5) AS delta_fips, ROUND(p.delta_state, 5) AS delta_state, t.num
                FROM combined_pop p, target t
                WHERE p.year=t.year
                    AND p.location_id IN
                        (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
                ORDER BY year ASC
            """
            context["ioi"] = json.dumps("Population")
        elif ioi == "hpi":
            select_query = """
                WITH target_hpi AS (
                    SELECT year, location_id, (((hpia/hpib) - 1) * 100) AS change
                    FROM (SELECT a.year, b.location_id, b.hpi AS hpib, a.hpi AS hpia
                        FROM (
                            SELECT year, location_id, hpi
                            FROM michaelrodelo.housing_prices
                            WHERE location_id=:fips) b 
                    INNER JOIN (
                        SELECT year, location_id, hpi
                        FROM michaelrodelo.housing_prices
                        WHERE location_id=:fips) a
                    ON b.year=a.year-1)),
                state_hpis AS (
                    SELECT *
                    FROM michaelrodelo.housing_prices
                    WHERE location_id IN 
                        (SELECT fips 
                        FROM michaelrodelo.location 
                        WHERE statename = 
                            (SELECT statename 
                            FROM michaelrodelo.location
                            WHERE fips=:fips))
                    ORDER BY location_id ASC),
                delta_state AS (
                    SELECT year, AVG(delta) AS change
                    FROM (
                        SELECT a.year AS year, (((a.hpi/b.hpi)-1)*100) AS delta
                        FROM state_hpis b LEFT JOIN state_hpis a
                        ON b.location_id=a.location_id
                            AND b.year=a.year-1)
                    WHERE year IS NOT NULL
                    GROUP BY year),
                combined_hpi AS (
                    SELECT target_hpi.year, target_hpi.location_id, target_hpi.change AS delta_fips, delta_state.change AS delta_state
                    FROM target_hpi, delta_state
                    WHERE delta_state.year=target_hpi.year
                    ORDER BY year ASC),
                target AS (
                    SELECT yr.year, location_id, COUNT(event_type) AS num
                    FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM events) yr
                    LEFT JOIN michaelrodelo.events e ON
                        EXTRACT(YEAR FROM e.event_date)=yr.year
                        AND location_id=:fips AND event_type IN (:torn, :hail, :wind)
                    GROUP BY yr.year, location_id)
                SELECT t.year, ROUND(h.delta_fips, 5) AS delta_fips, ROUND(h.delta_state, 5) AS delta_state, t.num
                FROM combined_hpi h, target t
                WHERE h.year=t.year
                    AND h.location_id IN
                        (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
                ORDER BY year ASC
            """
            context["ioi"] = json.dumps("HPI")
        else:
            select_query = """
                WITH allyears AS (
                    SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM michaelrodelo.events),
                allevents AS (
                    SELECT allyears.year, event_type
                    FROM allyears LEFT JOIN michaelrodelo.events e
                        ON EXTRACT(YEAR FROM e.event_date)=allyears.year
                        AND location_id=:fips),
                events1 AS (
                    SELECT allyears.year, COUNT(event_type) AS tornado
                    FROM allyears LEFT JOIN allevents e
                        ON e.year=allyears.year AND event_type=:torn
                    GROUP BY  allyears.year
                    ),
                events2 AS (
                    SELECT allyears.year, COUNT(event_type) AS hail
                    FROM allyears LEFT JOIN allevents e
                        ON e.year=allyears.year AND event_type=:hail
                    GROUP BY  allyears.year
                    ),
                events3 AS (
                    SELECT allyears.year, COUNT(event_type) AS wind
                    FROM allyears LEFT JOIN allevents e
                        ON e.year=allyears.year AND event_type=:wind
                    GROUP BY  allyears.year)
                SELECT * FROM events1 NATURAL JOIN events2 NATURAL JOIN events3 ORDER BY year
            """
            context["ioi"] = json.dumps("WX vs WX")
            wx_vs_wx = True
        context["wx_vs_wx"] = wx_vs_wx
        query_items = dict(fips=fips, torn=tornado, hail=hail, wind=wind)
        res = cursor.execute(select_query, query_items)
        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
            the_chart["data3"].append(item[3])
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
    return render(request, 'WebsiteDesign/OneFips.html', context=context)


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
        "data3": [],
        "data4": [],
    }
    state1 = "AK"
    state2 = "WY"
    if request.method == "POST":
        for key, val in request.POST.items():
            print(key, val)
        state1 = request.POST["state1"]
        state2 = request.POST["state2"]
        the_chart["d1state"] = json.dumps(state1)
        the_chart["d2state"] = json.dumps(state2)

        query_items = (state1, state1, state2, state2)
        select_query = """
            SELECT s1.year, s1.pop, s1.events, s2.pop, s2.events
            FROM
                (SELECT p.year AS year, total_population AS pop, events
                FROM
                    (SELECT sum(p.population) as total_population, l.statename, p.year
                    FROM michaelrodelo.populations p
                    INNER JOIN michaelrodelo.location l 
                    ON p.location_id = l.fips
                    WHERE statename = (:1)      
                    GROUP BY l.statename, p.year) p
                INNER JOIN
                    (SELECT statename, year, sum(num) AS events
                    FROM michaelrodelo.location l 
                        INNER JOIN 
                        (SELECT yr.year, location_id, COUNT(event_type) AS num
                        FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year 
                            FROM michaelrodelo.events) yr 
                        LEFT JOIN michaelrodelo.events e
                        ON EXTRACT(YEAR FROM e.event_date)=yr.year
                        GROUP BY yr.year, location_id) e
                    ON l.fips = e.location_id
                    WHERE statename = (:2)     
                    GROUP BY statename, year) e
                ON p.year = e.year) s1
            INNER JOIN
                (SELECT p.year AS year, total_population AS pop, events
                FROM
                    (SELECT sum(p.population) as total_population, l.statename, p.year
                    FROM michaelrodelo.populations p
                    INNER JOIN michaelrodelo.location l 
                    ON p.location_id = l.fips
                    WHERE statename = (:3)      
                    GROUP BY l.statename, p.year) p
                INNER JOIN
                    (SELECT statename, year, sum(num) AS events
                    FROM michaelrodelo.location l 
                        INNER JOIN 
                        (SELECT yr.year, location_id, COUNT(event_type) AS num
                        FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year 
                            FROM michaelrodelo.events) yr 
                        LEFT JOIN michaelrodelo.events e
                        ON EXTRACT(YEAR FROM e.event_date)=yr.year
                        GROUP BY yr.year, location_id) e
                    ON l.fips = e.location_id
                    WHERE statename = (:4)     
                    GROUP BY statename, year) e
                ON p.year = e.year) s2
            ON s1.year = s2.year   
            ORDER BY s1.year ASC   
        """
        res = cursor.execute(select_query, query_items)
        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
            the_chart["data3"].append(item[3])
            the_chart["data4"].append(item[4])
            context["d3hide"] = 0
            context["d4hide"] = 0
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
