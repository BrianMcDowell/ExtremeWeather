from django.shortcuts import render
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
    return render(request, 'WebsiteDesign/MainPage.html')


def one_fips(request):
    context = {}
    conn = oracledb_conn()
    cursor = conn.cursor()
    the_chart = {
        "yr": [],
        "data1": [],
        "data2": [],
    }

    if request.method == "POST":
        """
        Obtain query items from request.POST
        for loop below prints all POST items for validation
        """
        for key, val in request.POST.items():
            print(key, val)
        select_query = """
            WITH target AS (
                SELECT yr.year, location_id, COUNT(event_type) AS num
                FROM (SELECT DISTINCT EXTRACT(YEAR FROM event_date) AS year FROM events) yr LEFT JOIN 
                events e
                ON EXTRACT(YEAR FROM e.event_date)=yr.year
                    AND location_id=20173
                    AND event_type IN ('TORN', 'HAIL', 'WIND')
                GROUP BY yr.year, location_id)
            SELECT t.year, p.population, t.num
            FROM populations p, target t
            WHERE p.year=t.year AND p.location_id IN 
                (SELECT DISTINCT location_id FROM target WHERE location_id IS NOT NULL)
            ORDER BY year"""
        res = cursor.execute(select_query)
        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
        context["the_chart"] = the_chart

    location_data = []
    location_res = cursor.execute(
        """
        SELECT fips, countyname, statename
        FROM location
        ORDER BY fips ASC
        """
    )
    for location in location_res:
        location_data.append([location[0], location[1], location[2]])
    context["location_data"] = location_data
    conn.close()
    return render(request, '', context=context)


def two_fips(request):
    context = {}
    conn = oracledb_conn()
    cursor = conn.cursor()
    the_chart = {
        "yr": [],
        "data1": [],
        "data2": [],
    }

    if request.method == "POST":
        """
        Obtain query items from request.POST
        for loop below prints all POST items for validation
        """
        for key, val in request.POST.items():
            print(key, val)
        select_query = """
            WITH allevents AS (
                SELECT 
                    EXTRACT(MONTH FROM event_date) AS mon,
                    EXTRACT(YEAR FROM event_date) AS yr,
                    location_id, event_type
                FROM events
                WHERE location_id=20173 OR location_id=48439),
            e1 AS (
                SELECT mon, AVG(num1) AS avg1 FROM (
                    SELECT yr, mon, COUNT(event_type) as num1
                    FROM allevents
                    WHERE location_id=20173
                    GROUP BY yr, mon)
                GROUP BY mon),
            e2 AS (
                SELECT mon, AVG(num2) AS avg2 FROM (
                    SELECT yr, mon, COUNT(event_type) as num2
                    FROM allevents
                    WHERE location_id=48439
                    GROUP BY yr, mon)
                GROUP BY mon),
            allmonths AS (
                SELECT DISTINCT EXTRACT(MONTH FROM event_date) AS mon FROM events)
            SELECT allmonths.mon AS mon, COALESCE(avg1, 0), COALESCE(avg2, 0)
            FROM (allmonths LEFT JOIN e1 ON  e1.mon=allmonths.mon) LEFT JOIN e2 ON allmonths.mon=e2.mon
            ORDER BY mon ASC
        """
        res = cursor.execute(select_query)
        for item in res:
            the_chart["yr"].append(item[0])
            the_chart["data1"].append(item[1])
            the_chart["data2"].append(item[2])
        context["the_chart"] = the_chart

    location_data = []
    location_res = cursor.execute(
        """
        SELECT fips, countyname, statename
        FROM location
        ORDER BY fips ASC
        """
    )
    for location in location_res:
        location_data.append([location[0], location[1], location[2]])
    context["location_data"] = location_data
    conn.close()
    return render(request, '', context=context)
