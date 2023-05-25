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
  width: 250px;
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
  top: 36px;
  left: 5px;
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
  top: 71px;
  left: 330px;
  color: #505050;
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
