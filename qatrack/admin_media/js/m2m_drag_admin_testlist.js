/*
Allows drag and drop reordering of many to many fields (related by intermediary models)
in the admin. Starting point was http://djangosnippets.org/snippets/1053/
*/

function set_order(grouping){
    var order = 0;
    $(grouping).find('tr').each(function(i) {

        if ($(this).find("td[class^=field-] input").val() && !$(this).find("input[id$=DELETE]").is(":checked")){
            $(this).find('input[id$=order]').val(order);
            order +=1;
        }else{
            $(this).find('input[id$=order]').val("");
        }
    });

    var rows = $("#member-container tbody tr");
    $(rows).not(".add-row").removeClass("row1 row2")
        .filter(":even").addClass("row1").end()
        .filter(rows + ":odd").addClass("row2");
}

function sort_container(){
    var table = $("#member-container tbody");
    var rows = table.children('tr');
    rows.sort(function(a, b) {
        var ordera =  $(a).find('input[id$=order]').val();
        var orderb =  $(b).find('input[id$=order]').val();
        if (ordera === "") {
          ordera = 1000;
          if ($(a).find('input[id^=id_testlistmem]').length === 0){
            // push empty sublists to bottom
            ordera += 1;
          }
        }
        if (orderb === "") {
          orderb = 1000;
          if ($(b).find('input[id^=id_testlistmem]').length === 0){
            // push empty sublists to bottom
            ordera += 1;
          }
        }

        if(ordera > orderb) {
            return 1;
        }
        if(ordera < orderb) {
            return -1;
        }
        return 0;
    });
    rows.detach().appendTo(table);
    $(table.find(".add-row").get().reverse()).detach().appendTo(table);

}

function move_rows(){

    var item_sel = '#testlistmembership_set-group tr[class*=dynamic-], #children-group tr[class*=dynamic-]';
    var items = $(item_sel);

    var table = $("#member-container tbody");
    items.each(function(i, el){
      var type;
      if ($(el).find('input[id^=id_testlistmem]').length > 0){
        type = "Test";
      }else{
        type = "Sublist";
        $(el).find("td").eq(3).before("<td>--</td>");
      }
      $(el).find("td").eq(0).before("<td>" + type + "</td>");
      $(el).detach().appendTo(table);
    });
    sort_container();
}


$(document).ready(function() {

    var item_sel = '#member-container tr[class*=dynamic-]';

    /*set up dragabble membership list*/
    $('form').sortable({
        containment: '#member-container tbody',
        zindex: 10,
        items: item_sel,
        handle: 'td',
        update: function() {
          set_order(this)
        }
    });

    var firstGroup = $(".inline-group").eq(0);
    var container = $([
      '<div class="inline-group" id="member-container">',
      '  <div class="tabular inline-related">',
      '    <fieldset class="module">',
      '      <h2>Test List Members</h2>',
      '      <table>',
      '        <thead><th>Type</th><th colspan="2">ID</th><th>Order</th><th>Macro Name</th><th>Delete</th></thead>',
      '        <tbody></tbody>',
      '      </table>',
      '    </fieldset>',
      '  </div>',
      '</div>'
    ].join("")).insertBefore(firstGroup);

    move_rows();
    var table = $("#member-container tbody");
    var addRows = $('#testlistmembership_set-group tr.add-row, #children-group tr.add-row').detach().appendTo(table);
    addRows.children("td").attr("colspan", "6");
    addRows.find("a").on("click", function(e){
      move_rows();
    })

    table.find("td.original p").text("");
    table.find("tr.has_original td").css("padding-top", "8px");

    var origContainers = $('#testlistmembership_set-group,  #children-group');
    origContainers.find(".errorlist").detach().insertAfter($("#member-container fieldset h2"));
    origContainers.hide();

    /*change cursor to "move" when over table cells*/
    $('div.inline-related td').css('cursor', 'move');

    /*hides the ordering header*/
    $('div.inline-related').find('th:contains("Order")').hide();

    /*hides the ordering inputs*/
    $('div.inline-related').find('input[id$=order]').parent('td').hide();

    /*need to reset the order on submit otherwise an inline that was created
    may not have it's order value set*/
    $('form').submit(function(){set_order($('div.inline-group'));});

    $('div.inline-related').sort();

});
