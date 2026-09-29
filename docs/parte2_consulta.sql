-- Enunciado:
-- Obtener los nombres de los clientes los cuales tienen inscrito algún producto
-- disponible sólo en las sucursales que visitan.
--
-- Interpretación:
-- Cliente inscrito a un producto tal que TODAS las sucursales donde ese producto
-- está disponible son sucursales que el cliente ha visitado.

SELECT DISTINCT c.nombre
FROM cliente c
INNER JOIN inscripcion i ON i.idCliente = c.id
WHERE NOT EXISTS (
    SELECT 1
    FROM disponibilidad d
    WHERE d.idProducto = i.idProducto
      AND NOT EXISTS (
          SELECT 1
          FROM visitas v
          WHERE v.idCliente = c.id
            AND v.idSucursal = d.idSucursal
      )
);
