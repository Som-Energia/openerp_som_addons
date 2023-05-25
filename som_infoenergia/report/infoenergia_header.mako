## -*- coding: utf-8 -*-
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8"/>
</head>
<body>
<style>
    <%
       name = customer['name'] + customer['surname']
    %>
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
  width: 235px;
  display: block;
  padding-bottom: 5px;
  overflow: hidden;
}
%if len(name) > 30:
  .username {
    font-size: 0.6em;
  }
%endif
.useradress {
  position:absolute;
  top: 35px;
  left: 0px;
  %if len(customer['address']) > 85:
      font-size: 0.6em;
  %else:
      font-size: 0.8em;
  %endif
  width: 230px;
}
.usercups {
  position: absolute;
  font-size: 0.8em;
  top: 70px;
  left: 285px;
  color: #505050;
}
.username {
  position: absolute;
  left: 0px;
}
</style>
<div class="absolute">
    <span class="username">
    <strong>${name}</strong>
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
