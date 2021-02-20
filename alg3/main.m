clear all;
close all;

% Параметры ---------------------------------------------------------------
R = 0.75; % приведённая интенсивность
N = 10000; % кол-во заявок
M = 2; % длина очереди
limmited_queue = false; % с ограниченной очередью

% параметр входного распределения
lambda_in = 100;
X_in = exprnd(1/lambda_in,1,N);
% параметры выходных распределений
lambda_out = 133.3;
X_out = exprnd(1/lambda_out,1,N);

% Определение основных характеристик CМО ----------------------------------
QM = 0; % максимальная длина очереди
QA = 0; % средняя длина очереди
QZ = 0; % число заявок, поступивших на обслуживание без очереди
QT = 0; % среднее время пребывания заявки в очереди, (включая нулевые входы)
QX = 0; % среднее время пребывания заявки в очереди, (без нулевых входов)
FR = 0; % коэффициент загрузки
FT = 0; % среднее время обслуживания заявки
Rejected = 0; % количество отклонённых заявок

% определение абсолютного времени прихода заявки
for i=2:N
    X_in(i) = X_in(i-1)+X_in(i);
end

% вспомогательные параметры
curr_query = []; % текущая очередь, хранящая время попадания заявки в очередь
next_in = 1; % индекс следующего кандидата на вход
next_out = 1; % индекс следующего кандидата на выход
processed = 0; % количество обработанных заявок
curr_time = 0; % текущее время
is_open = true; % готов к обработке
last_query_change_time = 0; % время последнего изменения очереди
QA_summ_time = 0;

while processed+Rejected~=N
    if is_open % если обработчки готов принять заявку
        if ~isempty(curr_query) % если в очереди есть элементы
            % берётся первый элемент из очереди
            elem = curr_query(1);
            % изменение очереди
            QA = QA + length(curr_query)*(curr_time-last_query_change_time);
            QA_summ_time = QA_summ_time + (curr_time-last_query_change_time);
            last_query_change_time = curr_time;
            if length(curr_query)==1
                curr_query = [];
            else
                curr_query = curr_query(2:length(curr_query));
            end
            processed = processed + 1; % ещё одна заявка обработана
            is_open = false; % обработчик занят
            QT = QT + (curr_time - elem); % пребывани заявки в очереди
        else % очередь пуста
            % берётся первая пришедшая заявку в систему
            elem = X_in(next_in);
            next_in = next_in+1;
            processed = processed + 1; % ещё одная заявка обработана
            FR=FR+(elem-curr_time); % время простоя обработчика
            % изменение очереди
            QA_summ_time = QA_summ_time + elem - last_query_change_time;
            last_query_change_time = elem;
            curr_time = elem; % новое текущее время = время прихода заявки
            is_open = false; % обработчик занят
            QZ = QZ + 1; % количество заявок, обработанных без очереди
        end
    else % если обработчик занят
        % время, когда обработчик освободится
        curr_time = curr_time+X_out(next_out);
        next_out = next_out+1;
        % просмотр заявок, пришедших за время обработки заявки
        while next_in <= N && X_in(next_in) <= curr_time
            if (~limmited_queue) || (length(curr_query) < M) % если очередь неограничена или в очереди есть место
                % изменение очереди
                QA = QA + length(curr_query)*(X_in(next_in)-last_query_change_time);
                QA_summ_time = QA_summ_time + (X_in(next_in)-last_query_change_time);
                last_query_change_time = X_in(next_in);
                curr_query = [curr_query X_in(next_in)]; % добавление заявки в очередь
            else % очередь переполнена
                Rejected = Rejected + 1; % заявка отклонена
            end
            next_in = next_in+1;
        end
        is_open = true; % обработчик готов принят заявку
        if(length(curr_query)>QM)
            QM=length(curr_query); % максимальная длина очереди
        end
    end
end
QA = QA/(QA_summ_time); % средняя длина очереди
QX = QT/(N-QZ-Rejected); % среднее время пребывания заявки в очереди, (без нулевых входов)
QT = QT/(N-Rejected); % среднее время пребывания заявки в очереди, (включая нулевые входы)
FT = sum(X_out(1:next_out))/(N-Rejected); % среднее время обслуживания заявки
FR = 1-(FR/(curr_time+X_out(next_out))); % коэффициент загрузки


