## -*- coding: utf-8 -*-
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
</head>
<body>
<style>
.absolute {
  position: absolute;
  top: 56px;
  left: 305px;
  right: 0;
  width: 600px;
  height: 120px;
  color: #3F3F3F;
  font-family: Open Sans;
  font-size: 0.75em;
  line-height: 18px;
}
.username, .useradress, .usercups {
  width: 300px;
  display: block;
  padding-bottom: 5px;
}
.useradress {
  position:absolute;
  top: 36px;
  left: 5px;
  font-size: 0.8em;
  width: 230px;
}
.usercups {
  position: absolute;
  top: 71px;
  left: 252px;
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