// SCRIPT PARA LA CREACION DE LA BASE DE DATOS 	
    
    // Crear colección para Clientes
	db.createCollection("clientes")

	// Crear colección para Sucursales
	db.createCollection("sucursales")

	// Crear colección para Productos
	db.createCollection("productos")

	// Crear colección para Inscripciones
	db.createCollection("inscripciones")

	// Crear colección para Disponibilidad
	db.createCollection("disponibilidad")

	// Crear colección para visitas cliente–sucursal
	db.createCollection("visitas")

	// Crear coleccione para ver el historial de transacciones
	db.createCollection("transacciones")



		// Insertar datos en la colección Clientes
		db.clientes.insertMany([
		  { "id": 1, "nombre": "Juan", "apellidos": "Pérez", "ciudad": "Bogotá" },
		  { "id": 2, "nombre": "María", "apellidos": "García", "ciudad": "Medellín" }
		]);

		// Insertar datos en la colección Sucursales
		db.sucursales.insertMany([
		  { "id": 1, "nombre": "Sucursal Bogotá", "ciudad": "Bogotá" },
		  { "id": 2, "nombre": "Sucursal Medellín", "ciudad": "Medellín" }
		]);

		// Insertar datos en la colección Productos
		db.productos.insertMany([
		  { "id": 1, "nombre": "FPV_BTG_PACTUAL_RECAUDADORA", "monto_minimo": 75000, "categoria": "FPV" },
		  { "id": 2, "nombre": "FPV_BTG_PACTUAL_ECOPETROL", "monto_minimo": 125000, "categoria": "FPV" },
		  { "id": 3, "nombre": "DEUDAPRIVADA", "monto_minimo": 50000, "categoria": "FIC" },
		  { "id": 4, "nombre": "FDO-ACCIONES", "monto_minimo": 250000, "categoria": "FIC" },
		  { "id": 5, "nombre": "FPV_BTG_PACTUAL_DINAMICA", "monto_minimo": 100000, "categoria": "FPV" }
		]);

		// Insertar datos en la colección Inscripciones
		db.inscripciones.insertMany([
		  { "idCliente": 1, "idProducto": 1 },
		  { "idCliente": 1, "idProducto": 2 },
		  { "idCliente": 2, "idProducto": 3 }
		]);

		// Insertar datos en la colección Disponibilidad
		db.disponibilidad.insertMany([
		  { "idSucursal": 1, "idProducto": 1 },
		  { "idSucursal": 1, "idProducto": 2 },
		  { "idSucursal": 2, "idProducto": 3 }
		]);

		// Insertar datos en la colección visitas
		db.visitas.insertMany([
		  { "idSucursal": 1, "idCliente": 1, "fechaVisita": ISODate("2024-10-01T00:00:00Z") },
		  { "idSucursal": 2, "idCliente": 2, "fechaVisita": ISODate("2024-10-05T00:00:00Z") }
		]);


				// Verificar clientes
				db.clientes.find().pretty()

				// Verificar sucursales
				db.sucursales.find().pretty()

				// Verificar productos
				db.productos.find().pretty()

				// Verificar inscripciones
				db.inscripciones.find().pretty()

				// Verificar disponibilidad
				db.disponibilidad.find().pretty()

				// Verificar visitas
				db.visitas.find().pretty()


						// Obtener los nombres de los clientes que tienen inscrito algún producto disponible sólo en las sucursales que visitan
						db.visitas.aggregate([
						  {
							$lookup: {
							  from: "disponibilidad",
							  localField: "idSucursal",
							  foreignField: "idSucursal",
							  as: "productosDisponibles"
							}
						  },
						  { $unwind: "$productosDisponibles" },
						  {
							$lookup: {
							  from: "inscripciones",
							  localField: "productosDisponibles.idProducto",
							  foreignField: "idProducto",
							  as: "inscripcionesCliente"
							}
						  },
						  { $unwind: "$inscripcionesCliente" },
						  {
							$lookup: {
							  from: "clientes",
							  localField: "inscripcionesCliente.idCliente",
							  foreignField: "id",
							  as: "cliente"
							}
						  },
						  { $unwind: "$cliente" },
						  {
							$group: {
							  _id: "$cliente.id",
							  nombreCliente: { $first: "$cliente.nombre" },
							  apellidosCliente: { $first: "$cliente.apellidos" },
							  productos: { $addToSet: "$productosDisponibles.idProducto" },
							  sucursalesVisitadas: { $addToSet: "$idSucursal" }
							}
						  }
						]);


