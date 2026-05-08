const fs = require('fs');

// Fix contractors.ejs
let c = fs.readFileSync('/opt/snapatask/dashboard/views/contractors.ejs', 'utf8');

// Fix phone HTML rendering
c = c.replace(
  "<%=lead.phone||'<span class=\"text-muted\">hidden</span>'%>",
  "<%- lead.phone || '<span class=\"text-muted\">hidden</span>' %>"
);

// Fix &amp; in company names
c = c.replace(
  'title="<%=lead.company_name%>"><%=lead.company_name||\'—\'%>',
  'title="<%=lead.company_name%>"><%- (lead.company_name||"—").replace(/&amp;/g,"&") %>'
);

fs.writeFileSync('/opt/snapatask/dashboard/views/contractors.ejs', c);
console.log('contractors.ejs fixed');

// Fix home.ejs company names
let h = fs.readFileSync('/opt/snapatask/dashboard/views/home.ejs', 'utf8');
h = h.replace(
  '<%= c.company_name||\'—\' %>',
  '<%- (c.company_name||"—").replace(/&amp;/g,"&") %>'
);
fs.writeFileSync('/opt/snapatask/dashboard/views/home.ejs', h);
console.log('home.ejs fixed');

// Fix outreach.ejs lead names
let o = fs.readFileSync('/opt/snapatask/dashboard/views/outreach.ejs', 'utf8');
o = o.replace(
  '><%=log.lead_name||\'—\'%><',
  '><%- (log.lead_name||"—").replace(/&amp;/g,"&") %><'
);
fs.writeFileSync('/opt/snapatask/dashboard/views/outreach.ejs', o);
console.log('outreach.ejs fixed');

console.log('All fixes applied!');
