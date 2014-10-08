<html>
    <head>
        <style type="text/css">
            ${css}
        </style>
    </head>
    <body>
        %for o in objects :
            <%
               setLang(template_data['lang'])
               not data['fiscalyear'] and removeParentNode('para')
               not (data['period_from'] and data['period_to']) and removeParentNode('para')
            %>
            <div id="contenedor">            
                <div id="header">
                    <h1>
                        ${template_data['name']}              
                    </h1>
                    <div class="act_as_table">
                        <div class="act_as_row">
                            <div class="act_as_cell">
                                ${data['fiscalyear']}
                            </div>
                            <div class="act_as_cell" style="text-align:right;">
                                Periods: from ${data['period_from']} to ${data['period_to']}
                            </div>
                        </div>
                    </div>           
                </div>
                 
                <li style="list-style-type: ">
                <div id="contenidos">     
                    <div>
                        ${user.company_id.currency_id.name}
                    </div> 
                    <div class="act_as_table">
                        %for o in template_data['statements'][0]:
                            <div class="act_as_row"> 
                                <div class="act_as_cell" style="text-indent: ${o['indent']}pt; 
                                                                padding-top: ${o['top_spacing']}pt; 
                                                                font-weight: ${o['decoration_bold']};
                                                                text-decoration: ${o['decoration']}; 
                                                                font-style: ${o['font_name']};
                                                                padding-bottom: ${o['padding']}px; 
                                                                padding-top: ${o['padding']}px;"> 
                                        ${o['name'] or ''}
                                </div>
                               <div class="act_as_cell" style="text-align:right; 
                                                        margin-top: ${o['top_spacing']}pt;
                                                        font-weight: ${o['decoration_bold']};
                                                        text-decoration: ${o['decoration']};
                                                        font-style: ${o['font_name']};">
                                   ${formatLang(float(o['total_amount']))}                             
                               </div>
                            </div>      
                         %endfor           
                    </div>
                </div>
            </div>       
        %endfor
    </body>
</html>      