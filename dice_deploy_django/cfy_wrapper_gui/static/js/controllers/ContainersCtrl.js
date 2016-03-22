app.controller('ContainersCtrl', function($scope, RestServices, PopupServices, FileUploader, $timeout,
                                          Notification, $interval, $sce, $filter) {
    //
	// FILE UPLOAD CONFIG
    //
    $scope.uploader = new FileUploader({
        alias: 'file'  // form field name
    });
    FileUploader.FileSelect.prototype.isEmptyAfterSelection = function() {  // angular-file-upload bugfix [https://github.com/nervgh/angular-file-upload/wiki/FAQ#4-no-file-chosen-or-re-add-same-file]
        return true;
    };
    $scope.uploader.onCompleteItem = function(fileItem, response, status, headers) {
        $timeout(function(){
            $scope.uploader.clearQueue();
            $scope.syncContainers();
        }, 500);  // some delay to show progressbar
    };
    $scope.initUploader = function(cont){
        $scope.uploader.clearQueue();
        $scope.uploader.upload_errors = undefined;
        $scope.uploader.url = BLUEPRINT_UPLOAD_URL_TEMPLATE.replace('{id}', cont.id);
        $scope.uploader.containerId = cont.id;
    };
    $scope.uploader.filters.push({
        name: 'excelFilter',
        fn: function(item /*{File|FileLikeObject}*/, options) {
            var type = '|' + item.type.slice(item.type.lastIndexOf('/') + 1) + '|';
            var typeXGzip = 'x-gzip';
            var typeGzip = 'gzip';
            var allowedTypes = '|' + typeXGzip + '|' + typeGzip + '|';
            var isTypeOK = allowedTypes.indexOf(type) !== -1;

            var sizeLimitMB = 20.0;
            var sizeMB = item.size/1024/1024;
            var isSizeOK = sizeMB < sizeLimitMB;

            return isTypeOK && isSizeOK;
        }
    });
    $scope.uploader.onWhenAddingFileFailed = function(item /*{File|FileLikeObject}*/, filter, options) {
        $scope.uploader.upload_errors = 'Only .tar.gz files (<20 MB) can be uploaded';
    };


    //
    // BUTTON CALLBACKS
    //
	$scope.addContainer = function(){
        PopupServices.popupAddContrainer().then(function(data){
            var cont = RestServices.containers.save(data, function(){
                $scope.containers.unshift(cont);
            }, $scope.showServerError);

		});


	};

	$scope.removeContainer = function(cont){
		PopupServices.popupConfirm('Are you sure that you want to REMOVE CONTAINER with id <br><code>' + cont.id + '</code>?').then(function(){
			RestServices.container.delete(cont, function(){
                $scope.containers.splice($scope.containers.indexOf(cont), 1);
			}, $scope.showServerError);
		});

	};

    $scope.undeployBlueprint = function(cont){
        PopupServices.popupConfirm('Are you sure that you want to UNDEPLOY BLUEPRINT with id <br><code>' + cont.blueprint.cfy_id + '</code>?').then(function(){
			RestServices.blueprint.delete(cont.blueprint, function(){
                $scope.syncContainers();
			}, $scope.showServerError);
		});
    };

    $scope.redeployBlueprint = function(cont){
        PopupServices.popupConfirm('Are you sure that you want to REDEPLOY BLUEPRINT with id <br><code>' + cont.blueprint.cfy_id + '</code>?').then(function(){
			RestServices.containerBlueprint.put(cont, function(){
                $scope.syncContainers();
			}, $scope.showServerError);
		});
    };

    //
    // UTILS
    //
    $scope.showServerError = function(err){
        Notification.error(err.status + ': ' + err.data.msg);
    };
    $scope.getContainers = function(){
        $scope.containers = RestServices.containers.query({}, function(){
            //LOG('containers: ', $scope.containers);
        });
    };
    $scope.syncContainers = function(){
        var actualContainers = RestServices.containers.query({}, function(){

            console.log('Sync containers');

            // update currently shown containers without clearing whole list
            var actualContainersDict = {};
            var removedContainers = [];
            actualContainers.forEach(function(cont, idx){
                actualContainersDict[cont.id] = cont;
            });

            // a - update shown containers
            $scope.containers.forEach(function(cont, idx){
                if(actualContainersDict[cont.id] != undefined){
                    $scope.containers[idx] = actualContainersDict[cont.id];
                    actualContainersDict[cont.id].synced = true;
                }else{
                    removedContainers.push(cont);
                }
            });
            // b - remove removed containers
            removedContainers.forEach(function(cont, idx){
                $scope.containers.splice($scope.containers.indexOf(cont), 1);
            });
            // c - add added containers
            actualContainers = actualContainers.filter(function(el){return !el.synced;});
            $scope.containers.push.apply($scope.containers, actualContainers);

        });
    };
    $scope.isBlueprintDeployed = function(blueprint){
        if(!blueprint) return false;
        return blueprint.state_name == BLUEPRINT_STATES.completedStateName;
    };
    $scope.getBlueprintDatetimeStr = function(blueprint){
        if(blueprint) {
            return parseDateTime(blueprint.modified_date).local().format(C_dtFormatGUI);
        }
    };
    $scope.convertOutputs = function(blueprint){
        var data = blueprint.outputs;
        if(data){
            $filter('json')(data, 4);
            return $sce.trustAsHtml(data);
        }

    };


    //
    // ON LOAD
    //
	$scope.getContainers();
    $scope.blueprintStates = jQuery.extend({}, BLUEPRINT_STATES);

    //
    // PERIODIC
    //
    $interval(function(){
        $scope.syncContainers();
    }, 10000);

});
