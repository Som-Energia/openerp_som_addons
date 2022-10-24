## -*- coding: utf-8 -*-
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
</head>
<body>
<style>
.absolute {
  position: absolute;
  top: 98px;
  left: 349px;
  right: 0;
  width: 600px;
  height: 120px;
  color: #3F3F3F;
  font-family: Open Sans;
  font-size: 1em;
  line-height: 18px;
}
.username, .useradress, .usercups {
  width: 300px;
  display: block;
  padding-bottom: 5px;
}
.usercups {
  position: absolute;
  /* top: 98px; */
  left: 330px;
}
</style>
<div class="absolute">
    <span class="username">
    <strong>${customer['name']} ${customer['surname']}</strong>
    </span>
    <span class="useradress">
    ${customer['address']}
    </span>
    <span class="usercups">
    <strong>${customer['cups']}</strong>
    </span>
</div>
</body>
</html>