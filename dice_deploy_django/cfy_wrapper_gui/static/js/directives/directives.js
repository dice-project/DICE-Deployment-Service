app.directive('blueprintStatus', function() {
	return {
		restrict: 'E', // Use as element
		scope: { // Isolate scope
            currState: '=',      //string
            allStates: '='  // this is our utitlity object that stores config data
            /*
            e.g. allStates = {
                    stateNames: [
                        'pending',
                        'uploaded',
                        'ready_to_deploy',
                        'preparing_deploy',
                        'working',
                        'deployed'
                    ],
                    statePrettyNames: [
                        {prettyName: 'Upload', stateNames: ['pending']},
                        {prettyName: 'Prepare for deploy', stateNames: ['uploaded, ready_to_deploy', 'preparing_deploy']},
                        {prettyName: 'Deploy', stateNames: ['working']}
                    ],
                    completedStateName: 'deployed'
                };
             */
		},
		template: "<div class='btn-group dice-state-group' ></div>", // We need a div to attach to
		link: function(scope, elem) {

            function createSingleStateElement(state_pretty_name, cssClass){
                var el = angular.element('<button class="btn btn-default dice-state-single">' +
                    state_pretty_name + '</button>');
                el.addClass(cssClass);
                return el;
            }

            // find pretty idx of current state
            var currIdx = -1;
            for(var i=0; i<scope.allStates.statePrettyNames.length; i++){
                var prettyObj = scope.allStates.statePrettyNames[i];
                if(prettyObj.stateNames.indexOf(scope.currState) >= 0){
                    currIdx = i;
                    break;
                }
            }
            if(scope.currState == scope.allStates.completedStateName){
                currIdx = scope.allStates.statePrettyNames.length; // one more than max index
            }


            var stateGroupDiv = $(elem).children()[0];
            for(var i=0; i<scope.allStates.statePrettyNames.length; i++){
                var cssClass = 'dice-state-not-yet';
                if(i < currIdx){
                    cssClass = 'dice-state-already';
                }else if(i == currIdx){
                    cssClass = 'dice-state-currently';
                }

                createSingleStateElement(scope.allStates.statePrettyNames[i].prettyName, cssClass).
                appendTo(stateGroupDiv);
            }

		}
	};
});