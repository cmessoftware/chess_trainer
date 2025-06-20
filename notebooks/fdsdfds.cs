public async Task<List<MorososTransmitResultDto>?> GetByExpressionAsync(Expression<Func<MorososTransmit, bool>> expression, int pageNumber, int pageSize = 1000)
{
    try
    {
        var query = _context.MorososTransmits
            .AsNoTracking()
            .Where(expression)
            .Join(
            _context.MorososTransmitOks.AsNoTracking(),
            m => new { m.IdTransmit, m.IdCliente },
            m0 => new { m0.IdTransmit, m0.IdCliente },

            (m, m0) => new { m, m0 }
            )
            .Join(
            _context.MorososCategorias.AsNoTracking(),
            x => new { x.m0.IdCategoria, x.m0.IdCliente },
            m1 => new { m1.IdCategoria, m1.IdCliente },
            (x, m1) => new { x.m, x.m0, m1 }
            )
            .Join(
            _context.Entidades.AsNoTracking(),
            x => new { x.m.IdEntidad, x.m.IdCliente },
            e => new { e.IdEntidad, e.IdCliente },
            (x, e) => new { x.m, x.m0, x.m1, e }
            )
            .Join(
            _context.MorososRegiones.AsNoTracking(),
            x => new { x.m.IdRegion, x.m.IdCliente },
            m2 => new { m2.IdRegion, m2.IdCliente },
            (x, m2) => new { x.m, x.m0, x.m1, x.e, m2 }
            )
            .OrderByDescending(x => x.m0.IdCliente)
            .ThenByDescending(x => x.m0.IdTransmit)
            .ThenByDescending(x => x.m0.NroDoc)
            .Skip((pageNumber - 1) * pageSize)
            .Take(pageSize);

        var response = await query
                        .Select(x => new MorososTransmitResultDto
                        {
                            CreateDate = x.m.CreateDate,
                            CreateUser = x.m.CreateUser,
                            IdCliente = x.m.IdCliente,
                            IdRegion = x.m.IdRegion,
                            Cuil = x.m0.Cuil,
                            NroDoc = x.m0.NroDoc,
                            ApellidoNombre = x.m0.ApellidoNombre,
                            RazonSocial = x.e.RazonSocial,
                            Telefono = x.e.Telefono ?? string.Empty,
                            NombreRegion = x.m2.NombreRegion,
                            NombreCategoria = x.m1.NombreCategoria,
                            Periodo = x.m.Periodo,
                            IdEntidad = x.e.IdEntidad
                        }).ToListAsync();

        return response;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error en la consulta: {ex.Message}");
        Console.WriteLine($"StackTrace: {ex.StackTrace}");
        throw;
    }
}
