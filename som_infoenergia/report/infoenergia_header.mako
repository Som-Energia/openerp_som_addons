<html
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
}
</style>
<div class="absolute">
<span style="font-family: Open Sans; font-size: 1.1em; line-height: 18px">
<span style="font-weight:bold">
${customer['name']}
<br>${customer['surname']}
</span>
<br>${customer['address']}
<br><span style="font-weight:bold">CUPS ${customer['cups']}</span>
</span>
</div>
</body>
</html>