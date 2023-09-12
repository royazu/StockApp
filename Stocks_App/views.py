from datetime import datetime
from django.shortcuts import render
from django.db import connection


# Create your views here.
def home(request):
	return render(request, 'home.html')


def result(request):
	with connection.cursor() as cursor:
		cursor.execute("""          
                SELECT I.Name, ROUND(SUM(money), 3) as TotalSum
				FROM EXP E, Investor I
				WHERE E.NAME = I.NAME
				GROUP BY I.Name
				ORDER BY [TotalSum] DESC
        """)
		sql_res1 = dictfetchall(cursor)
		cursor.execute("""
				SELECT S.Symbol, I.Name, S.hold as Quantity
				FROM strongHolders S, Investor I
				WHERE S.ID=I.ID
				ORDER BY Symbol, Name
		""")
		sql_res2 = dictfetchall(cursor)
		cursor.execute("""
				SELECT B.tDate, MTT.Symbol, I.Name
				FROM Buying B INNER JOIN moreThanThree MTT ON B.Symbol = MTT.Symbol, Investor I
				WHERE B.ID = I.ID
				ORDER BY tDate, Name
		""")
		sql_res3 = dictfetchall(cursor)
		return render(request, 'result.html',
		              {'sql_res1': sql_res1, 'sql_res2': sql_res2, 'sql_res3': sql_res3})


def insert(request):
	with connection.cursor() as cursor:

		id_error = True

		if request.method == 'POST' and request.POST:

			id = int(request.POST['id'])
			sum = request.POST['sum']

			cursor.execute("""
					SELECT ID, AvailableCash
					FROM INVESTOR
				""")
			getAC = dictfetchall(cursor)
			for t in getAC:
				if t['ID'] == id:
					id_error = False
					AC = t['AvailableCash']


			if not id_error:
				matched = False
				today = datetime.today().strftime("%Y-%m-%d")
				cursor.execute("""
					SELECT *
					FROM Transactions
				""")
				check = dictfetchall(cursor)
				for t in check:
					if t['ID'] == id and str(t['tDate']) == today:
						matched = True
						PrevTransAmount = int(t['TQuantity'])
				if not matched:
					cursor.execute("""
		                    INSERT INTO Transactions
		                    VALUES (""" +"'"+ today + "'" + """, """ + str(id) + """, """ + str(sum) + """);
		            """)
					newAC = int(AC) + int(sum)
					cursor.execute("""
							UPDATE Investor
							SET AvailableCash = """ + str(newAC) + """
							WHERE ID=""" + str(id) + """;
					""")
				else:
					cursor.execute("""
							UPDATE Transactions
							SET TQuantity = """ + str(sum) + """
							WHERE ID=""" + str(id) + """ AND tDate = """ +"'"+ today +"'"+ """;
					""")

					newAC = int(AC) - PrevTransAmount + int(sum)
					cursor.execute("""
							UPDATE Investor
							SET AvailableCash = """ + str(newAC) + """
							WHERE ID=""" + str(id) + """;
					""")

		else:
			id_error = False

		cursor.execute("""   
				SELECT TOP 10 *
				FROM Transactions
				ORDER BY tDate DESC, ID DESC
	    """)
		sql_res = dictfetchall(cursor)
		return render(request, 'insert.html', {'sql_res': sql_res, 'id_error': id_error})


def buy(request):
	with connection.cursor() as cursor:
		error = False
		iid_error = True
		csymbol_error = True
		funds_error = False
		match_error = False
		purchased = False
		if request.method == 'POST' and request.POST:

			iid = int(request.POST['iid'])
			sym = request.POST['csymbol']
			amount = request.POST['quantity']
			today = datetime.today().strftime("%Y-%m-%d")

			cursor.execute("""
					SELECT ID, AvailableCash
					FROM INVESTOR
				""")
			check = dictfetchall(cursor)
			for t in check:
				if t['ID'] == iid:
					iid_error = False
					ac = t['AvailableCash']

			cursor.execute("""
					select Stock.Symbol, dt, price
					from (
				    select Symbol, MAX(tDate) dt
				    from Stock
				    group by Symbol) currentPrices, Stock
					where Stock.Symbol = currentPrices.Symbol and dt = tDate
			""")
			check = dictfetchall(cursor)
			matched_date = False
			for t in check:
				if str(t['Symbol']) == str(sym):
					csymbol_error = False
					cp = t['price']
					dt = t['dt']
					if str(dt) == today:
						matched_date = True

			if not iid_error and not csymbol_error:
				nac = float(ac) - float(cp) * float(amount)
				if nac < 0:
					funds_error = True
				else:

					cursor.execute("""
						SELECT *
						FROM Buying
					""")
					check = dictfetchall(cursor)
					for t in check:
						if t['ID'] == iid and str(t['tDate']) == today:
							match_error = True

					if not match_error:

						if not matched_date:
							cursor.execute("""
							INSERT INTO Stock
							VALUES (""" + "'" + str(sym) + "'" + """, """ + "'" + today + "'" + """, """ + str(cp) + """);
							""")

						cursor.execute("""
						UPDATE Investor
						SET AvailableCash = """ + str(nac) + """
						WHERE ID=""" + str(iid) + """;
						""")

						cursor.execute("""
						INSERT INTO Buying
						VALUES (""" + "'" + today + "'" + """, """ + str(
							iid) + """, """ + "'" + str(sym) + "'" + """, """ + str(amount) + """);
						""")
						purchased = True

			if funds_error or iid_error or csymbol_error or match_error:
				error = True
		cursor.execute("""   
				select top 10 Stock.tDate, ID, Stock.Symbol, BQuantity*Price as Payed
				from Buying inner join stock on Buying.Symbol = Stock.Symbol and Buying.tDate = Stock.tDate
				order by payed desc ,ID desc;
	    """)
		sql_res = dictfetchall(cursor)
		return render(request, 'buy.html',
		              {'sql_res': sql_res, 'error': error, 'iid_error': iid_error, 'funds_error': funds_error,
		               'csymbol_error': csymbol_error, 'purchased': purchased, 'match_error': match_error})


def dictfetchall(cursor):
	# ￼￼  "Return all rows from a cursor as a dict"
	columns = [col[0] for col in cursor.description]
	return [dict(zip(columns, row)) for row in cursor.fetchall()]
