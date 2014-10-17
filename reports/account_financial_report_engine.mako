<html>
    <head>
        <style type="text/css">
             .overflow_ellipsis {
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
            }
            ${css}
        </style>
    </head>
    <body>
        %for o in objects: 
            <% setLang(template_data['lang']) %>
            <div class="name">
               ${template_data['name']} - ${user.company_id.name} - ${user.company_id.currency_id.name}          
            </div>
            <div class="act_as_table data_table">
                <div class="act_as_row labels">
                    <div class="act_as_cell">${_('Fiscal Year')}</div>
                    <div class="act_as_cell">${_('Periods Filter')}</div>
                    <div class="act_as_cell">${_('Journal Filter')}</div>
                </div>
                <div class="act_as_row">
                    <div class="act_as_cell">${ data['fiscalyear'] or '-' }</div>
                    <div class="act_as_cell">
                        ${_('From:')}
                        ${data['period_from'] if data['period_from'] else ''}
                        ${_('To:')}
                        ${data['period_to'] or 'u' }
                    </div>
                    <div class="act_as_cell">
                        ${data['state']}
                    </div>
                </div>
            </div>
            <div id="contenedor" style="margin-top:3%;">
                <div class="act_as_table list_table">                   
                    %for o in template_data['statements'][0]:     
                        <div class="act_as_row lines"> 
                            <div class="act_as_cell grande" style="width: 80%; text-indent: ${o['indent']}pt;
                                                                padding-top: ${o['top_spacing']}pt; 
                                                                font-weight: ${o['decoration_bold']};
                                                                text-decoration: ${o['decoration']}; 
                                                                font-style: ${o['font_name']};
                                                                padding-bottom: ${o['padding']}px; 
                                                                background-color:${o['background']};"> 
                                ${o['name'] or ''}
                            </div>
                            <div class="act_as_cell chica" style="text-align:right;
                                                        margin-top: ${o['top_spacing']}pt;
                                                        font-weight: ${o['decoration_bold']};
                                                        text-decoration: ${o['decoration']};
                                                        font-style: ${o['font_name']};
                                                        background-color:${o['background']}">
                                %if o['category_title'] != 'false':
                                    ${formatLang(float(o['total_amount']))}
                                %endif                              
                            </div>
                        </div>                 
                    %endfor
                </div>
            </div>       
        %endfor
    </body>
</html>      