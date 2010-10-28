//table nonsense
    $(document).ready(function() 
        { 
            $("#myTable").tablesorter();
            $("#myTable tr:even").addClass("rowEven");
            $("#myTable tr")
                .mouseover(function(){$(this).addClass("rowOver");})
                .mouseout(function(){$(this).removeClass("rowOver");})
                .click(function(){
                    $("#myTable tr").removeClass("rowSelect").find(".forgethint").slideUp();
                    $(this).addClass("rowSelect").find(".forgethint").slideDown();
                });
            $("#myTable th")
                .mouseover(function(){$(this).addClass("thOver");})
                .mouseout(function(){$(this).removeClass("thOver");});
            $("#myTable .forgethint a").click(function(){
                    $(this).closest("tr").fadeOut().addClass("forgotten");
                    zebraStripe();               
                })
                .mouseover(function(){$(this).closest("tr").animate({backgroundColor: "#f66"}, 500);})
                .mouseout(function(){$(this).closest("tr").stop(true, true)
                    .animate({backgroundColor: "#f5e0e0"}, {
                        duration: 250, 
                        complete:function(){
                            $(this).css({"background-color": null});
                        }
                    });
                });
                
            $("#myTable th").click(function(){
                setTimeout("zebraStripe()", 1);
                });
        } 
    
    );
    
    function zebraStripe() {
        $("#myTable tr:not(.forgotten):even").addClass("rowEven")
        $("#myTable tr:not(.forgotten):odd").removeClass("rowEven")  
    }

