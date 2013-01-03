var module = angular.module("censorwatch", [], function($routeProvider, $locationProvider) {
  $locationProvider.html5Mode(true);
});

module.factory('search', function() {
    return function search(query, callback) {
        $.ajax({
            url: "/classifications",
            dataType: "json",
            method: "get",
            data: query,
            success: callback
        });
    };
});



function ClassificationsCtrl($scope, search, $location) {
    $scope.sidebarVisible = true;
    $scope.tableClass = "span9";
    $scope.query = $location.search();

    function reset() {
        $scope.page = 0;
        $scope.rows = [];
        $scope.pages = [];
        $scope.totalResults = "(total unimplemented)";
        $scope.query.count = $scope.query.count || 20;
    }
    reset();

    $scope.anyCriteria = function() {
        for (prop in $scope.query) {
            if (prop == "page" || prop == "count") {
                continue;
            }
            
            if ($scope.query[prop] != "") {
                console.log($scope.query[prop], prop);
                return true;
            }
        }

        return false;
    };

    $scope.toggleSidebar = function() {
        $scope.tableClass = ($scope.sidebarVisible = !$scope.sidebarVisible) ? "span9" : "span12";
    };
    
    $scope.getResultSpan = function() {
        var count = parseInt($scope.query.count, 10),
            start = ($scope.page - 1) * count + 1,
            end = start + count - 1;
        return start + "-" + end;
    };

    function changePage() {
        if ($scope.pages[$scope.page] == null) {
            $scope.query.page = $scope.page;
            search($scope.query, function(data) {
                $scope.$apply(function() {
                   $scope.pages[$scope.page] = data.results;
                   $scope.rows = $scope.pages[$scope.page];
                });
            });

        } else {
            $scope.rows = []
            $scope.rows = $scope.pages[$scope.page];
            console.log("sync", $scope.rows);
        }
    }

    $scope.previousPage = function() {
        $scope.page = Math.max(1, $scope.page - 1);
        changePage();
    };
    
    $scope.nextPage = function() {
        $scope.page++;
        changePage();
    };

    $scope.removeCriterion = function(criterion) {
        delete $scope.query[criterion];
        reset();
        changePage();
    }

    // init
    $scope.nextPage();
}

function ClassificationCtrl($scope) {
  $scope.goBack = function() {
    history.go(-1);
  }

  function getData() {
    $.ajax({
        url: location.pathname,
        dataType: "json",
        method: "get",
        success: function(data) {
            $scope.$apply(function() {
                $scope.rows = data;
            });
        }
    });
  }

  getData();
}
