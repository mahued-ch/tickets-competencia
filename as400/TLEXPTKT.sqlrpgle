**free
///
// @Program TLEXPTKT
//
// @Purpose - Exportación de Tickets SAPRCTGH a IFS
//
// @author mahued
// @Date 19 jun 2026
// Copyright (c)
//
// Change Log:
// Tag      Date        User             Description
//
///

ctl-opt dftactgrp(*no) actgrp(*caller) option(*srcstmt:*nodebugio) bnddir('QC2LE');

// Programa : TCKEXPJS
// Tipo     : SQLRPGLE / ILE RPG Free compatible con IBM i V7R2
// Objetivo : Exportar SA/SAPRCTGH, SA/SAPRCTGD y SA/SAPRCTGDI a JSON en IFS
// Nota     : Todas las lineas de comentario usan doble slash //
// Parametro opcional: pLastRun char(14) con formato YYYYMMDDHHMMSS
// Si pLastRun viene blanco o no se pasa, exporta carga completa

dcl-pi *n;
  pLastRun char(14) const options(*nopass);
end-pi;

// APIs C para IFS

dcl-pr open int(10) extproc('open');
  path pointer value options(*string);
  oflag int(10) value;
  mode uns(10) value options(*nopass);
  ccsid uns(10) value options(*nopass);
end-pr;

dcl-pr write int(10) extproc('write');
  fd int(10) value;
  buffer pointer value;
  bytes uns(10) value;
end-pr;

dcl-pr close int(10) extproc('close');
  fd int(10) value;
end-pr;

dcl-pr Qp0lSetAttr int(10) extproc('Qp0lSetAttr');
  path pointer value options(*string);
  attr int(10) value;
  buf pointer value;
  bufLen int(10) value;
end-pr;

dcl-pr unlink int(10) extproc('unlink');
  path pointer value options(*string);
end-pr;

dcl-pr exit extproc('exit');
  status int(10) value;
end-pr;

// Constantes IFS. En V7R2 validar contra QSYSINC/H/FCNTL si tu ambiente difiere

dcl-c O_WRONLY    2;
dcl-c O_CREAT     8;
dcl-c O_TRUNC     64;
dcl-c MODE_0666   438;
dcl-c CCSID_UTF8  1208;
dcl-c QP0L_ATTR_CCSID 327;

dcl-c BASE_DIR    '/tickets/inbound/';
dcl-c SOURCE_SYS  'AS400';
dcl-c LAYOUT_VER  '1.0';

// Variables generales

dcl-s batchCode    char(15);
dcl-s generatedAt  char(25);
dcl-s startTs      timestamp;
dcl-s endTs        timestamp;
dcl-s hasLast      ind inz(*off);
dcl-s lastDate     packed(8:0) inz(0);
dcl-s lastTime     packed(6:0) inz(0);

dcl-s headerFile   varchar(128);
dcl-s itemsFile    varchar(128);
dcl-s storesFile   varchar(128);
dcl-s controlFile  varchar(128);
dcl-s headerPath   varchar(512);
dcl-s itemsPath    varchar(512);
dcl-s storesPath   varchar(512);
dcl-s controlPath  varchar(512);

dcl-s headerCnt    int(10) inz(0);
dcl-s itemCnt      int(10) inz(0);
dcl-s storeCnt     int(10) inz(0);
dcl-s filesWritten int(10) inz(0);

// Host variables SAPRCTGH

dcl-s h_DGHTCK char(35);
dcl-s h_DGHCOD char(10);
dcl-s h_DGHSTR packed(5:0);
dcl-s h_DGHDAT packed(8:0);
dcl-s h_DGHHRS packed(6:0);
dcl-s h_DGHZON packed(3:0);
dcl-s h_DGHTDA packed(5:0);
dcl-s h_DGHSUC packed(5:0);
dcl-s h_DGHUSR char(10);
dcl-s h_DGHSTS char(1);

// Host variables SAPRCTGD

dcl-s d_DGDTCK char(35);
dcl-s d_DGDCOD char(10);
dcl-s d_DGDSTR packed(5:0);
dcl-s d_DGDDAT packed(8:0);
dcl-s d_DGDHRS packed(6:0);
dcl-s d_DGDSKU packed(18:0);
dcl-s d_DGDDPT packed(3:0);
dcl-s d_DGDSDP packed(3:0);
dcl-s d_DGDCLS packed(3:0);
dcl-s d_DGDSCL packed(3:0);
dcl-s d_DGDPRC packed(9:2);
dcl-s d_DGDPRV packed(10:0);
dcl-s d_DGDUPC packed(18:0);
dcl-s d_DGDSTS char(1);

// Host variables SAPRCTGDI

dcl-s i_DGITCK char(35);
dcl-s i_DGICOD char(10);
dcl-s i_DGISTR packed(5:0);
dcl-s i_DGIDAT packed(8:0);
dcl-s i_DGIHRS packed(6:0);
dcl-s i_DGITDA packed(5:0);
dcl-s i_DGISTS char(1);

exec sql set option commit = *none, closqlcsr = *endmod, datfmt = *iso;

monitor;
  startTs = %timestamp();
  batchCode = makeBatchCode(startTs);
  generatedAt = makeGeneratedAt(startTs);

  headerFile  = 'header_'  + %trim(batchCode) + '.json';
  itemsFile   = 'items_'   + %trim(batchCode) + '.json';
  storesFile  = 'stores_'  + %trim(batchCode) + '.json';
  controlFile = 'control_' + %trim(batchCode) + '.json';

  headerPath  = BASE_DIR + headerFile;
  itemsPath   = BASE_DIR + itemsFile;
  storesPath  = BASE_DIR + storesFile;
  controlPath = BASE_DIR + controlFile;

  logMsg('Inicio exportacion. Batch=' + %trim(batchCode));

  if %parms() >= 1 and %trim(pLastRun) <> '';
    if %len(%trim(pLastRun)) <> 14;
      fail('Parametro pLastRun invalido. Use YYYYMMDDHHMMSS.');
    endif;
    lastDate = %dec(%subst(pLastRun:1:8):8:0);
    lastTime = %dec(%subst(pLastRun:9:6):6:0);
    hasLast = *on;
    logMsg('Filtro incremental DGHDAT/DGHHRS > ' + %trim(pLastRun));
  else;
    hasLast = *off;
    logMsg('Sin filtro incremental. Carga completa.');
  endif;

  buildSelection();

  exec sql select count(*) into :headerCnt from QTEMP.TCKEXPSEL;

  if headerCnt = 0;
    logMsg('No hay tickets para exportar. No se generan archivos.');
    return;
  endif;

  exec sql
    select count(*) into :itemCnt
      from SA.SAPRCTGD d
      join QTEMP.TCKEXPSEL k
        on k.TCK = d.DGDTCK and k.COD = d.DGDCOD and k.STR = d.DGDSTR
       and k.DAT = d.DGDDAT and k.HRS = d.DGDHRS;

  exec sql
    select count(*) into :storeCnt
      from SA.SAPRCTGDI i
      join QTEMP.TCKEXPSEL k
        on k.TCK = i.DGITCK and k.COD = i.DGICOD and k.STR = i.DGISTR
       and k.DAT = i.DGIDAT and k.HRS = i.DGIHRS;

  if itemCnt = 0 or storeCnt = 0;
    fail('Control de calidad fallo: lote sin items o sin tiendas.');
  endif;

  writeHeaderFile();
  filesWritten += 1;
  writeItemsFile();
  filesWritten += 1;
  writeStoresFile();
  filesWritten += 1;
  writeControlFile();
  filesWritten += 1;

  endTs = %timestamp();
  logMsg('Fin exportacion. Inicio=' + %char(startTs) + ' Fin=' + %char(endTs));
  logMsg('Cabeceras=' + %char(headerCnt) + ' Items=' + %char(itemCnt) +
         ' Tiendas=' + %char(storeCnt) + ' Archivos=' + %char(filesWritten));

on-error;
  cleanupPartialFiles();
  logMsg('ERROR no controlado. Se eliminaron archivos parciales.');
endmon;

return;

// Crear seleccion congelada de tickets validos
// Como las tablas reales no tienen fecha de alta, se usa fecha/hora del ticket

// Crear tabla fisica de seleccion en QTEMP
// QTEMP es propia del job, por lo que no hay choque entre ejecuciones

dcl-proc buildSelection;

  // Intentar eliminar la tabla si existe en este job
  // Si no existe, SQLCODE sera -204 y se ignora

  exec sql
    drop table QTEMP.TCKEXPSEL;

  // Crear tabla fisica en QTEMP

  exec sql
    create table QTEMP.TCKEXPSEL
    (
      TCK char(35) not null,
      COD char(10) not null,
      STR decimal(5,0) not null,
      DAT decimal(8,0) not null,
      HRS decimal(6,0) not null
    );

  // Crear indice para mejorar joins posteriores

  exec sql
    create index TCKEXPSEL1
      on QTEMP.TCKEXPSEL
      (
        TCK,
        COD,
        STR,
        DAT,
        HRS
      );

  if hasLast;

    exec sql
      insert into QTEMP.TCKEXPSEL
      select h.DGHTCK,
             h.DGHCOD,
             h.DGHSTR,
             h.DGHDAT,
             h.DGHHRS
        from SA.SAPRCTGH h
       where (
               h.DGHDAT > :lastDate
               or
               (
                 h.DGHDAT = :lastDate
                 and h.DGHHRS > :lastTime
               )
             )
         and exists
             (
               select 1
                 from SA.SAPRCTGD d
                where d.DGDTCK = h.DGHTCK
                  and d.DGDCOD = h.DGHCOD
                  and d.DGDSTR = h.DGHSTR
                  and d.DGDDAT = h.DGHDAT
                  and d.DGDHRS = h.DGHHRS
             )
         and exists
             (
               select 1
                 from SA.SAPRCTGDI i
                where i.DGITCK = h.DGHTCK
                  and i.DGICOD = h.DGHCOD
                  and i.DGISTR = h.DGHSTR
                  and i.DGIDAT = h.DGHDAT
                  and i.DGIHRS = h.DGHHRS
             );

  else;

    exec sql
      insert into QTEMP.TCKEXPSEL
      select h.DGHTCK,
             h.DGHCOD,
             h.DGHSTR,
             h.DGHDAT,
             h.DGHHRS
        from SA.SAPRCTGH h
       where exists
             (
               select 1
                 from SA.SAPRCTGD d
                where d.DGDTCK = h.DGHTCK
                  and d.DGDCOD = h.DGHCOD
                  and d.DGDSTR = h.DGHSTR
                  and d.DGDDAT = h.DGHDAT
                  and d.DGDHRS = h.DGHHRS
             )
         and exists
             (
               select 1
                 from SA.SAPRCTGDI i
                where i.DGITCK = h.DGHTCK
                  and i.DGICOD = h.DGHCOD
                  and i.DGISTR = h.DGHSTR
                  and i.DGIDAT = h.DGHDAT
                  and i.DGIHRS = h.DGHHRS
             );

  endif;

end-proc;

// Escribir header_*.json con todos los campos de SAPRCTGH

dcl-proc writeHeaderFile;
  dcl-s fd int(10);
  dcl-s first ind inz(*on);
  dcl-s line varchar(32740);

  exec sql declare C_HDR cursor for
    select h.DGHTCK,h.DGHCOD,h.DGHSTR,h.DGHDAT,h.DGHHRS,h.DGHZON,h.DGHTDA,h.DGHSUC,h.DGHUSR,h.DGHSTS
      from SA.SAPRCTGH h
      join QTEMP.TCKEXPSEL k
        on k.TCK=h.DGHTCK and k.COD=h.DGHCOD and k.STR=h.DGHSTR and k.DAT=h.DGHDAT and k.HRS=h.DGHHRS
     order by h.DGHDAT,h.DGHHRS,h.DGHTCK,h.DGHCOD,h.DGHSTR;

  fd = openFile(headerPath);
  writeLine(fd:'[');
  exec sql open C_HDR;

  dou sqlcode <> 0;
    exec sql fetch C_HDR into :h_DGHTCK,:h_DGHCOD,:h_DGHSTR,:h_DGHDAT,:h_DGHHRS,
                               :h_DGHZON,:h_DGHTDA,:h_DGHSUC,:h_DGHUSR,:h_DGHSTS;
    if sqlcode = 0;
      if not first;
        writeLine(fd:',');
      endif;
      first = *off;
      line = '  {' +
        '"source_ticket_code":"' + jsonEscape(%trimr(h_DGHTCK)) + '",' +
        '"source_business_code":"' + jsonEscape(%trimr(h_DGHCOD)) + '",' +
        '"source_store_code":"' + jsonEscape(%trim(%char(h_DGHSTR))) + '",' +
        '"source_ticket_date":"' + date8(h_DGHDAT) + '",' +
        '"source_ticket_time":"' + time6(h_DGHHRS) + '",' +
        '"source_status_code":"' + jsonEscape(%trimr(h_DGHSTS)) + '",' +
        '"payload":{"raw_fields":{' +
          '"DGHTCK":"' + jsonEscape(%trimr(h_DGHTCK)) + '",' +
          '"DGHCOD":"' + jsonEscape(%trimr(h_DGHCOD)) + '",' +
          '"DGHSTR":' + %trim(%char(h_DGHSTR)) + ',' +
          '"DGHDAT":' + %trim(%char(h_DGHDAT)) + ',' +
          '"DGHHRS":' + %trim(%char(h_DGHHRS)) + ',' +
          '"DGHZON":' + %trim(%char(h_DGHZON)) + ',' +
          '"DGHTDA":' + %trim(%char(h_DGHTDA)) + ',' +
          '"DGHSUC":' + %trim(%char(h_DGHSUC)) + ',' +
          '"DGHUSR":"' + jsonEscape(%trimr(h_DGHUSR)) + '",' +
          '"DGHSTS":"' + jsonEscape(%trimr(h_DGHSTS)) + '"' +
        '}}}';
      writeLine(fd:line);
    endif;
  enddo;

  exec sql close C_HDR;
  writeLine(fd:']');
  closeFile(fd);
end-proc;

// Escribir items_*.json con todos los campos de SAPRCTGD

dcl-proc writeItemsFile;
  dcl-s fd int(10);
  dcl-s first ind inz(*on);
  dcl-s line varchar(32740);

  exec sql declare C_DET cursor for
    select d.DGDTCK,d.DGDCOD,d.DGDSTR,d.DGDDAT,d.DGDHRS,d.DGDSKU,d.DGDDPT,d.DGDSDP,
           d.DGDCLS,d.DGDSCL,d.DGDPRC,d.DGDPRV,d.DGDUPC,d.DGDSTS
      from SA.SAPRCTGD d
      join QTEMP.TCKEXPSEL k
        on k.TCK=d.DGDTCK and k.COD=d.DGDCOD and k.STR=d.DGDSTR and k.DAT=d.DGDDAT and k.HRS=d.DGDHRS
     order by d.DGDDAT,d.DGDHRS,d.DGDTCK,d.DGDCOD,d.DGDSTR,d.DGDSKU;

  fd = openFile(itemsPath);
  writeLine(fd:'[');
  exec sql open C_DET;

  dou sqlcode <> 0;
    exec sql fetch C_DET into :d_DGDTCK,:d_DGDCOD,:d_DGDSTR,:d_DGDDAT,:d_DGDHRS,:d_DGDSKU,
                               :d_DGDDPT,:d_DGDSDP,:d_DGDCLS,:d_DGDSCL,:d_DGDPRC,:d_DGDPRV,
                               :d_DGDUPC,:d_DGDSTS;
    if sqlcode = 0;
      if not first;
        writeLine(fd:',');
      endif;
      first = *off;
      line = '  {' +
        '"source_ticket_code":"' + jsonEscape(%trimr(d_DGDTCK)) + '",' +
        '"source_business_code":"' + jsonEscape(%trimr(d_DGDCOD)) + '",' +
        '"source_store_code":"' + jsonEscape(%trim(%char(d_DGDSTR))) + '",' +
        '"source_ticket_date":"' + date8(d_DGDDAT) + '",' +
        '"source_ticket_time":"' + time6(d_DGDHRS) + '",' +
        '"product_code":"' + jsonEscape(%trim(%char(d_DGDSKU))) + '",' +
        '"unit_price":' + num2(d_DGDPRC) + ',' +
        '"source_status_code":"' + jsonEscape(%trimr(d_DGDSTS)) + '",' +
        '"payload":{"raw_fields":{' +
          '"DGDTCK":"' + jsonEscape(%trimr(d_DGDTCK)) + '",' +
          '"DGDCOD":"' + jsonEscape(%trimr(d_DGDCOD)) + '",' +
          '"DGDSTR":' + %trim(%char(d_DGDSTR)) + ',' +
          '"DGDDAT":' + %trim(%char(d_DGDDAT)) + ',' +
          '"DGDHRS":' + %trim(%char(d_DGDHRS)) + ',' +
          '"DGDSKU":' + %trim(%char(d_DGDSKU)) + ',' +
          '"DGDDPT":' + %trim(%char(d_DGDDPT)) + ',' +
          '"DGDSDP":' + %trim(%char(d_DGDSDP)) + ',' +
          '"DGDCLS":' + %trim(%char(d_DGDCLS)) + ',' +
          '"DGDSCL":' + %trim(%char(d_DGDSCL)) + ',' +
          '"DGDPRC":' + num2(d_DGDPRC) + ',' +
          '"DGDPRV":' + %trim(%char(d_DGDPRV)) + ',' +
          '"DGDUPC":' + %trim(%char(d_DGDUPC)) + ',' +
          '"DGDSTS":"' + jsonEscape(%trimr(d_DGDSTS)) + '"' +
        '}}}';
      writeLine(fd:line);
    endif;
  enddo;

  exec sql close C_DET;
  writeLine(fd:']');
  closeFile(fd);
end-proc;

// Escribir stores_*.json con todos los campos de SAPRCTGDI

dcl-proc writeStoresFile;
  dcl-s fd int(10);
  dcl-s first ind inz(*on);
  dcl-s line varchar(32740);

  exec sql declare C_DIS cursor for
    select i.DGITCK,i.DGICOD,i.DGISTR,i.DGIDAT,i.DGIHRS,i.DGITDA,i.DGISTS
      from SA.SAPRCTGDI i
      join QTEMP.TCKEXPSEL k
        on k.TCK=i.DGITCK and k.COD=i.DGICOD and k.STR=i.DGISTR and k.DAT=i.DGIDAT and k.HRS=i.DGIHRS
     order by i.DGIDAT,i.DGIHRS,i.DGITCK,i.DGICOD,i.DGISTR,i.DGITDA;

  fd = openFile(storesPath);
  writeLine(fd:'[');
  exec sql open C_DIS;

  dou sqlcode <> 0;
    exec sql fetch C_DIS into :i_DGITCK,:i_DGICOD,:i_DGISTR,:i_DGIDAT,:i_DGIHRS,:i_DGITDA,:i_DGISTS;
    if sqlcode = 0;
      if not first;
        writeLine(fd:',');
      endif;
      first = *off;
      line = '  {' +
        '"source_ticket_code":"' + jsonEscape(%trimr(i_DGITCK)) + '",' +
        '"source_business_code":"' + jsonEscape(%trimr(i_DGICOD)) + '",' +
        '"source_store_code":"' + jsonEscape(%trim(%char(i_DGISTR))) + '",' +
        '"source_ticket_date":"' + date8(i_DGIDAT) + '",' +
        '"source_ticket_time":"' + time6(i_DGIHRS) + '",' +
        '"applies_to_store_code":"' + jsonEscape(%trim(%char(i_DGITDA))) + '",' +
        '"source_status_code":"' + jsonEscape(%trimr(i_DGISTS)) + '",' +
        '"payload":{"raw_fields":{' +
          '"DGITCK":"' + jsonEscape(%trimr(i_DGITCK)) + '",' +
          '"DGICOD":"' + jsonEscape(%trimr(i_DGICOD)) + '",' +
          '"DGISTR":' + %trim(%char(i_DGISTR)) + ',' +
          '"DGIDAT":' + %trim(%char(i_DGIDAT)) + ',' +
          '"DGIHRS":' + %trim(%char(i_DGIHRS)) + ',' +
          '"DGITDA":' + %trim(%char(i_DGITDA)) + ',' +
          '"DGISTS":"' + jsonEscape(%trimr(i_DGISTS)) + '"' +
        '}}}';
      writeLine(fd:line);
    endif;
  enddo;

  exec sql close C_DIS;
  writeLine(fd:']');
  closeFile(fd);
end-proc;

// Escribir control_*.json al final

dcl-proc writeControlFile;
  dcl-s fd int(10);
  fd = openFile(controlPath);
  writeLine(fd:'{');
  writeLine(fd:'  "batch_code":"' + %trim(batchCode) + '",');
  writeLine(fd:'  "generated_at":"' + %trim(generatedAt) + '",');
  writeLine(fd:'  "source_system":"' + SOURCE_SYS + '",');
  writeLine(fd:'  "files":[');
  writeLine(fd:'    {"file_type":"HEADER","file_name":"' + jsonEscape(headerFile) +
  '","record_count":' + %char(headerCnt) + '},');
  writeLine(fd:'    {"file_type":"ITEM","file_name":"' + jsonEscape(itemsFile) +
  '","record_count":' + %char(itemCnt) + '},');
  writeLine(fd:'    {"file_type":"STORE","file_name":"' + jsonEscape(storesFile) +
  '","record_count":' + %char(storeCnt) + '}');
  writeLine(fd:'  ],');
  writeLine(fd:'  "layout_version":"' + LAYOUT_VER + '"');
  writeLine(fd:'}');
  closeFile(fd);
end-proc;

// Abrir archivo IFS binario; los bytes UTF-8 se escriben en writeLine

dcl-proc openFile;
  dcl-pi *n int(10);
    pPath char(512) const;
  end-pi;

  dcl-s fd int(10);
  dcl-s oflag int(10);
  dcl-s fileCcsid uns(10);

  oflag = O_WRONLY + O_CREAT + O_TRUNC;

  fd = open(%trim(pPath): oflag: MODE_0666);

  if fd < 0;
    fail('No se pudo abrir IFS: ' + %trim(pPath));
  endif;

  // Etiquetar el stream file como UTF-8 para herramientas IFS / consumidores
  fileCcsid = CCSID_UTF8;
  if Qp0lSetAttr(%trim(pPath): QP0L_ATTR_CCSID: %addr(fileCcsid):
                  %size(fileCcsid)) < 0;
    logMsg('Aviso: no se pudo fijar CCSID 1208 en ' + %trim(pPath));
  endif;

  return fd;

end-proc;

// Escribir linea: convierte EBCDIC del job a UTF-8 antes del write

dcl-proc writeLine;
  dcl-pi *n;
    pFd int(10) value;
    pText char(32740) const;
  end-pi;

  dcl-s outLine varchar(32740:4) ccsid(1208);
  dcl-s nl char(1) ccsid(1208) inz(x'0A');
  dcl-s rc int(10);
  dcl-s len uns(10);

  outLine = %trimr(pText) + nl;
  len = %len(outLine);

  rc = write(pFd: %addr(outLine: *data): len);

  if rc < 0 or rc <> len;
    fail('Error write IFS. Bytes=' + %char(len) + ' rc=' + %char(rc));
  endif;

end-proc;

// Cerrar stream file

dcl-proc closeFile;
  dcl-pi *n;
    pFd int(10) value;
  end-pi;
  if close(pFd) <> 0;
    fail('Error close IFS.');
  endif;
end-proc;

// Eliminar archivos parciales si falla antes del control

dcl-proc cleanupPartialFiles;
  unlink(%trim(headerPath));
  unlink(%trim(itemsPath));
  unlink(%trim(storesPath));
  unlink(%trim(controlPath));
end-proc;

// Finalizar con error controlado

dcl-proc fail;
  dcl-pi *n;
    pMsg varchar(1024) const;
  end-pi;
  logMsg('ERROR: ' + pMsg);
  cleanupPartialFiles();
  exit(1);
end-proc;

// Escapar caracteres especiales para JSON

// Escapar caracteres especiales para JSON

dcl-proc jsonEscape;
  dcl-pi *n varchar(32740);
    pIn varchar(32740) const;
  end-pi;

  dcl-s xout varchar(32740) inz('');
  dcl-s c char(1);
  dcl-s x int(10);
  dcl-s dq char(1) inz('"');
  dcl-s bs char(1) inz('\');

  for x = 1 to %len(%trimr(pIn));

    c = %subst(pIn:x:1);

    select;

      when c = dq;
        xout += bs + dq;

      when c = bs;
        xout += bs + bs;

      when c = x'25';
        xout += bs + 'n';

      when c = x'0D';
        xout += bs + 'r';

      when c = x'05';
        xout += bs + 't';

      other;
        xout += c;

    endsl;

  endfor;

  return xout;

end-proc;

// Formatear precio con punto decimal

dcl-proc num2;
  dcl-pi *n varchar(40);
    p packed(9:2) const;
  end-pi;
  dcl-s t varchar(40);
  t = %trim(%char(p));
  t = replaceAll(t: ',': '.');
  return t;
end-proc;

// Reemplazar un caracter por otro

dcl-proc replaceAll;
  dcl-pi *n varchar(32740);
    txt varchar(32740) const;
    from char(1) const;
    too char(1) const;
  end-pi;
  dcl-s xout varchar(32740) inz('');
  dcl-s c char(1);
  dcl-s x int(10);
  for x = 1 to %len(%trimr(txt));
    c = %subst(txt:x:1);
    if c = from;
      xout += too;
    else;
      xout += c;
    endif;
  endfor;
  return xout;
end-proc;

// Convertir fecha numerica YYYYMMDD a YYYY-MM-DD

dcl-proc date8;
  dcl-pi *n char(10);
    pDate packed(8:0) const;
  end-pi;
  dcl-s s char(8);
  s = %editc(pDate:'X');
  return %subst(s:1:4) + '-' + %subst(s:5:2) + '-' + %subst(s:7:2);
end-proc;

// Convertir hora numerica HHMMSS a HH:MM:SS

dcl-proc time6;
  dcl-pi *n char(8);
    pTime packed(6:0) const;
  end-pi;
  dcl-s s char(6);
  s = %editc(pTime:'X');
  return %subst(s:1:2) + ':' + %subst(s:3:2) + ':' + %subst(s:5:2);
end-proc;

// Generar batch YYYYMMDD_HHMMSS

dcl-proc makeBatchCode;
  dcl-pi *n char(15);
    pTs timestamp const;
  end-pi;
  return %char(%date(pTs):*iso0) + '_' + %char(%time(pTs):*iso0);
end-proc;

// Generar fecha/hora ISO 8601 con offset fijo -06:00

dcl-proc makeGeneratedAt;
  dcl-pi *n char(25);
    pTs timestamp const;
  end-pi;
  return %char(%date(pTs):*iso) + 'T' + %char(%time(pTs):*iso) + '-06:00';
end-proc;

// Enviar mensaje a job log mediante DSPLY

// Enviar mensaje a job log mediante DSPLY en bloques de 52 caracteres

dcl-proc logMsg;
  dcl-pi *n;
    pMsg varchar(1024) const;
  end-pi;

  dcl-s xmsg char(52);
  dcl-s xpos int(10) inz(1);
  dcl-s xlen int(10);
  dcl-s xtotal int(10);

  xtotal = %len(%trimr(pMsg));

  if xtotal = 0;
    xmsg = ' ';
    dsply xmsg;
    return;
  endif;

  dow xpos <= xtotal;

    xlen = xtotal - xpos + 1;

    if xlen > 52;
      xlen = 52;
    endif;

    xmsg = *blanks;
    %subst(xmsg:1:xlen) = %subst(pMsg:xpos:xlen);

    dsply xmsg;

    xpos += xlen;

  enddo;

end-proc;
 