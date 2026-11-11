'use strict';
const fs=require('fs');
const {triage}=require('./triage');
const input=JSON.parse(fs.readFileSync(process.argv[2] || require('path').join(__dirname,'demo_request.json'),'utf8'));
console.log(JSON.stringify(triage(input),null,2));
