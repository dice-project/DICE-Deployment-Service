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
            // start syncing again
            $scope.preventSync = false;
        }, 500);  // some delay to show progressbar
    };
    $scope.initUploader = function(cont){
        $scope.uploader.clearQueue();
        $scope.uploader.upload_errors = undefined;
        $scope.uploader.url = BLUEPRINT_UPLOAD_URL_TEMPLATE.replace('{id}', cont.id);
        $scope.uploader.containerId = cont.id;
        // prevent syncing while file picker is opened to prevent loss of selection
        $scope.preventSync = true;
    };
    $scope.uploader.filters.push({
        name: 'contentTypeFilter',
        fn: function(item /*{File|FileLikeObject}*/, options) {
            var sizeLimitMB = 20.0;
            var sizeMB = item.size/1024/1024;
            var isSizeOK = sizeMB < sizeLimitMB;

            return isSizeOK;
        }
    });
    $scope.uploader.onWhenAddingFileFailed = function(item /*{File|FileLikeObject}*/, filter, options) {
        $scope.uploader.upload_errors = 'Only .tar.gz and .yaml files (<20 MB) can be uploaded';
    };
    $scope.uploader.onAfterAddingFile = function(){
        // start syncing again
        $scope.preventSync = false;
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
        PopupServices.popupConfirm('Are you sure that you want to UNDEPLOY BLUEPRINT with id <br><code>' + cont.blueprint.id + '</code>?').then(function(){
			RestServices.blueprint.delete(cont.blueprint, function(){
                $scope.syncContainers();
			}, $scope.showServerError);
		});
    };

    $scope.redeployBlueprint = function(cont){
        PopupServices.popupConfirm('Are you sure that you want to REDEPLOY BLUEPRINT with id <br><code>' + cont.blueprint.id + '</code>?').then(function(){
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
        return blueprint.state_name == BLUEPRINT_DEPLOY_STATES.completedStateName;
    };
    $scope.isBlueprintUndeployed = function(blueprint){
        if(!blueprint) return false;
        return blueprint.state_name == BLUEPRINT_UNDEPLOY_STATES.completedStateName;
    };
    $scope.isBlueprintBeingDeployed = function(blueprint){
        if(!blueprint) return false;
        if($scope.isBlueprintDeployed(blueprint)) return false;
        return BLUEPRINT_DEPLOY_STATES.stateNames.indexOf(blueprint.state_name) >= 0;
    };
    $scope.isBlueprintBeingUndeployed = function(blueprint){
        if(!blueprint) return false;
        if($scope.isBlueprintUndeployed(blueprint)) return false;
        return BLUEPRINT_UNDEPLOY_STATES.stateNames.indexOf(blueprint.state_name) >= 0;
    };
    $scope.isBlueprintError = function(blueprint){
        if(!blueprint) return false;
        return blueprint.state_name == BLUEPRINT_ERROR_STATE;
    };
    $scope.getBlueprintDatetimeStr = function(blueprint){
        if(blueprint) {
            return $scope.getDatetimeStr(blueprint.modified_date);
        }
    };
    $scope.getDatetimeStr = function(date){
        return parseDateTime(date).local().format(C_dtFormatGUI);
    };
    $scope.convertOutputs = function(blueprint){
        var data = blueprint.outputs;
        if(data){
            $filter('json')(data, 4);
            return $sce.trustAsHtml(data);
        }
    };
    $scope.getPrettyStateName = function(stateId){
        for(var i=0; i<BLUEPRINT_DEPLOY_STATES.statePrettyNames.length; i++){
            var prettyObj = BLUEPRINT_DEPLOY_STATES.statePrettyNames[i];
            if(prettyObj.stateNames.indexOf(stateId) >= 0){
                return prettyObj.prettyName;
            }
        }
        for(var i=0; i<BLUEPRINT_UNDEPLOY_STATES.statePrettyNames.length; i++){
            var prettyObj = BLUEPRINT_UNDEPLOY_STATES.statePrettyNames[i];
            if(prettyObj.stateNames.indexOf(stateId) >= 0){
                return prettyObj.prettyName;
            }
        }
        return '(unknown state: ' + stateId + ')';
    };

    //
    // POPUPS
    //
    $scope.showContainerErrors = function(container){
        RestServices.containerErrors.query(container, function(errors){
            PopupServices.popupContainerErrors(container, errors, $scope);
        });
    };


    //
    // ON LOAD
    //
	$scope.getContainers();
    $scope.blueprintDeployStates = jQuery.extend({}, BLUEPRINT_DEPLOY_STATES);
    $scope.blueprintUndeployStates = jQuery.extend({}, BLUEPRINT_UNDEPLOY_STATES);

    //
    // PERIODIC
    //
    $scope.preventSync = false;
    $interval(function(){
        if(!$scope.preventSync){
            $scope.syncContainers();
        }else{
            console.log('Sync prevented');
        }

    }, 10000);

});
