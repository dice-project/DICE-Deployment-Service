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
		template: "<div class='dice-blueprint-statusbar'></div>", // We need a div to attach to
		link: function(scope, elem) {

            function createSingleStateElement(idx, state_pretty_name, cssClasses){
                var el = angular.element('<div class="dice-blueprint-state"><span class="dice-blueprint-state-num">' +
                    (idx + 1) + '</span>' + state_pretty_name + '</div>');
                cssClasses.forEach(function(cssClass){el.addClass(cssClass)});
                return el;
            }
            function createSeparatorElement(cssClasses){
                var el = angular.element('<div class="dice-blueprint-separator"></div>');
                cssClasses.forEach(function(cssClass){el.addClass(cssClass)});
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
                var isFinalState = i == scope.allStates.statePrettyNames.length - 1;
                var cssClasses = [];
                var separatorCssClasses = [];
                if(i < currIdx){
                    cssClasses.push('dice-blueprint-state-already');
                    separatorCssClasses.push('dice-blueprint-separator-already');
                }else if(i == currIdx){
                    cssClasses.push('dice-blueprint-state-currently');
                    separatorCssClasses.push('dice-blueprint-separator-currently');
                }else{
                    cssClasses.push('dice-blueprint-state-not-yet');
                    separatorCssClasses.push('dice-blueprint-separator-not-yet');
                }

                if(isFinalState){
                    cssClasses.push('dice-blueprint-state-final');
                }

                createSingleStateElement(i, scope.allStates.statePrettyNames[i].prettyName, cssClasses).
                appendTo(stateGroupDiv);

                if(!isFinalState) {
                    createSeparatorElement(separatorCssClasses).appendTo(stateGroupDiv);
                }
            }

		}
	};
});