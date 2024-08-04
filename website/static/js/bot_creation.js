document.addEventListener('DOMContentLoaded', function () {
    const button = document.getElementById('addDropdownButton');
    const hyperparamCheckbox = document.getElementById('hyperparamCheckbox');
    const hyperparamForm = document.getElementById('hyperparamForm');
    const mlModelSelect = document.getElementById('ml_model');
    const hyperparamFields = {
        linear_regression: ['learning_rate'],
        decision_tree: ['max_depth'],
        random_forest: ['num_trees', 'max_depth'],
        svm: ['kernel', 'c_value'],
        neural_network: ['learning_rate', 'num_layers']
    };

    const options = ['Moving Average', 'Exponential Moving Average', 'Moving Standard Deviation', 'MACD', 'RSI', 'Momentum', 'Periodic Lows', 'Periodic Highs', 'Bollinger Bands'];
    let dropdownCount = 1;

    hyperparamCheckbox.addEventListener('change', function () {
        if (hyperparamCheckbox.checked) {
            hyperparamForm.style.display = 'none';
        } else {
            hyperparamForm.style.display = 'block';
            updateHyperparamForm();
        }
    });

    mlModelSelect.addEventListener('change', updateHyperparamForm);

    button.addEventListener('click', function () {
        addDropdown();
    });

    function addDropdown() {
        const selectedValues = Array.from(document.querySelectorAll('select')).map(select => select.value);
        const availableOptions = options.filter(option => !selectedValues.includes(option));

        if (availableOptions.length > 0) {
            dropdownCount++;

            const formGroup = document.createElement('div');
            formGroup.className = 'form-group section';
            formGroup.id = `formGroup${dropdownCount}`;

            const label = document.createElement('h3');
            const labelElement = document.createElement('label');
            labelElement.setAttribute('for', `dropdown${dropdownCount}`);
            labelElement.textContent = `Add technical indicators as features for the model`;
            label.appendChild(labelElement);

            const select = document.createElement('select');
            select.id = `dropdown${dropdownCount}`;
            select.className = 'form-control';
            select.name = `technical_indicator_${dropdownCount}`;  // Set unique name
            select.addEventListener('change', updateAllDropdowns);

            availableOptions.forEach(option => {
                const newOption = document.createElement('option');
                newOption.value = option;
                newOption.textContent = option;
                select.appendChild(newOption);
            });

            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'delete_btn';
            deleteButton.innerHTML = '<img src="static/images/icons/trashcan.svg"></img>';
            deleteButton.addEventListener('click', function () {
                formGroup.remove();
                updateAllDropdowns();
            });

            formGroup.appendChild(label);
            formGroup.appendChild(select);
            formGroup.appendChild(deleteButton);
            document.getElementById('technicalIndicatorsSection').insertBefore(formGroup, button);
        }

        if (availableOptions.length <= 1) {
            button.style.display = 'none';
        } else {
            button.style.display = 'block';
        }
    }

    function updateAllDropdowns() {
        const selectsInTechnicalIndicatorsSection = document.querySelectorAll('#technicalIndicatorsSection select');
        const allSelectedValues = Array.from(selectsInTechnicalIndicatorsSection).map(select => select.value);

        selectsInTechnicalIndicatorsSection.forEach(select => {
            const currentValue = select.value;
            const availableOptions = options.filter(option => !allSelectedValues.includes(option) || option === currentValue);

            select.innerHTML = '';
            availableOptions.forEach(option => {
                const newOption = document.createElement('option');
                newOption.value = option;
                newOption.textContent = option;
                newOption.selected = option === currentValue;
                select.appendChild(newOption);
            });
        });

        const remainingOptions = options.filter(option => !allSelectedValues.includes(option));
        if (remainingOptions.length > 0) {
            button.style.display = 'block';
        } else {
            button.style.display = 'none';
        }
    }

    function updateHyperparamForm() {
        const selectedModel = mlModelSelect.value;
        const fieldsToShow = hyperparamFields[selectedModel] || [];

        document.querySelectorAll('.hyperparam-field').forEach(field => {
            if (fieldsToShow.includes(field.id)) {
                field.style.display = 'block';
            } else {
                field.style.display = 'none';
            }
        });
    }
});