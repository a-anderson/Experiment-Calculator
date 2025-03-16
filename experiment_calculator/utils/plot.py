from typing import Union, Literal
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc

def power_curve(
    calculation_type:Literal["Minimum Sample Size", "Required Sample Size"],
    x_data:Union[list, np.ndarray],
    power_percents:Union[list, np.ndarray],
    target_power_level:int,
    plot_type:str,
    outcome_type:Literal["binary", "normal"]
):
    if calculation_type == "Minimum Sample Size":
        x_label = "Required Sample Size"
        hover_label = "Sample Size"
    else:
        x_label = "Effect Size"
        hover_label = "Effect Size"

    title = f"Power Curve for the {x_label} for a {outcome_type.title()} Outcome"
    hover_template = f"Power: %{{y}}%<br>{hover_label}: %{{x:,}}"

    # find the corresponding location on the x-axis for the target power
    marker_x_value = x_data[power_percents.index(target_power_level)]

    # Create the power curve plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_data,
        y=power_percents,
        mode='lines',
        line=dict(color='royalblue', width=4),
        name=f'{x_label}',
        hovertemplate=hover_template,
        hoverlabel=dict(font=dict(size=20)),
        showlegend=False,
    ))

    # Add a marker for target power
    fig.add_trace(go.Scatter(
        x=[marker_x_value],
        y=[target_power_level],
        mode='markers',
        marker=dict(size=14, color='coral'),
        name=f'{x_label} for {target_power_level}% Power',
        hovertemplate=hover_template,
        hoverlabel=dict(font=dict(size=20)),
        showlegend=False
    ))

    # Add horizontal and vertical trace lines for target power
    fig.add_trace(go.Scatter(
        x=[0, marker_x_value],
        y=[target_power_level, target_power_level],
        mode='lines',
        line=dict(color='coral', dash='dash', width=4),
        name=f'Sample Size for {target_power_level}% Power',
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=[marker_x_value, marker_x_value],
        y=[0, target_power_level],
        mode='lines',
        line=dict(color='coral', dash='dash', width=4),
        name=f'Sample Size for {target_power_level}% Power',
        showlegend=False
    ))

    # Add axis labels and title
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title="Power (%)",
        template="plotly_white",
        yaxis=dict(showline=True, linecolor='grey', linewidth=1, range=[0, 100], title_font=dict(size=24), tickfont=dict(size=18)), # Display the x-axis line
        xaxis=dict(showline=True, linecolor='grey', linewidth=1, range=[0,max(x_data)], title_font=dict(size=24), tickfont=dict(size=18)),
        height=550,
        autosize=True,
    )

    return fig

def group_difference_forest(
    data:pd.DataFrame,
    outcome_type:Literal["binary", "normal"],
    effect_type:Literal["Absolute Effect", "Relative Effect"],
):

    data["error"] = (data["ci_upper"] - data["ci_lower"]) / 2
    data_reversed = data.iloc[::-1].reset_index(drop=True)

    # create figure
    fig = go.Figure()

    for i, row in data_reversed.iterrows():
        
        # set colours based on result significance and direction
        if row["ci_lower"] > 0:
            line_colour = 'royalblue'
        elif row["ci_upper"] < 0:
            line_colour = 'coral' 
        else:
            line_colour = 'lightgrey'

        # main plot with error bars
        fig.add_trace(go.Scatter(
            x=[row["point_estimate"]],
            y=[i],
            mode='markers',
            marker=dict(color='white', size=20, symbol='circle'),
            error_x=dict(
                type='data',
                symmetric=True,
                array=[row['error']],
                color=line_colour, 
                thickness=8,
            ),
            name=row['group_name'],
            hoverlabel=dict(font=dict(size=20)),
        ))

    # update marker with dark line around the point 
    fig.update_traces(
        marker=dict(size=20, symbol="circle", line=dict(width=3, color="black"))
    )

    # zero reference line
    fig.add_vline(x=0, line=dict(color='red', dash='dash'))

    if outcome_type == "normal" and effect_type == "Absolute Effect":
        x_axis_label = "Absolute Difference in Responses"
    else:
        if effect_type == "Absolute Effect":
            x_axis_label = "Absolute Difference in Responses (%)"
        else:
            x_axis_label = "Relative Difference in Responses (%)"

    # customise plot
    fig.update_layout(
        title='Difference in Outcome Between Groups',
        xaxis_title=x_axis_label,
        yaxis=dict(
            # autorange="reversed",
            title_font=dict(size=20), 
            tickfont=dict(size=18),   
            tickvals=list(range(len(data_reversed))), 
            ticktext=data_reversed['group_name'], 
            showline=True, 
            linecolor='lightgrey', 
            linewidth=1, 
            showgrid=False, 
            zeroline=False
        ),
        xaxis=dict(
            title_font=dict(size=20), 
            tickfont=dict(size=18),
            showline=True, 
            linecolor='lightgrey', 
            linewidth=1,
            showgrid=False
        ),
        showlegend=False,
        template='plotly_white'
    )
    
    return fig

def group_response_forest(
    data:pd.DataFrame,
    outcome_type:Literal["binary", "normal"],
):

    data["error"] = (data["ci_upper"] - data["ci_lower"]) / 2

    colors = pc.qualitative.Plotly
    num_groups = data.shape[0]

    # Create figure with one trace per study
    fig = go.Figure()

    for i, row in data.iterrows():
        
        # main plot with error bars
        fig.add_trace(go.Scatter(
            x=[row['point_estimate']],
            y=[i],
            mode='markers',
            marker=dict(
                symbol='circle', 
                size=20, 
                color=colors[(i + 2) % len(colors)], # i+2 to choose nicer colours
            ),  
            error_x=dict(
                type='data', 
                array=[row['error']], 
                thickness=8, 
                width=0, 
                color='lightgrey',
            ),
            name=row['group_name'],
            hoverlabel=dict(font=dict(size=20)),
        ))
    
    if outcome_type == "binary":
        x_axis_label = "Response Rate"
    else:
        x_axis_label = "Mean Outcome"

    # customise plot
    fig.update_layout(
        title='Group Responses with Confidence Intervals',
        xaxis_title=x_axis_label,
        xaxis=dict(
            title_font=dict(size=20), 
            tickfont=dict(size=18),
            showline=True, 
            linecolor='lightgrey', 
            linewidth=1, 
            showgrid=False
        ),
        yaxis=dict(
            autorange="reversed",
            title_font=dict(size=20), 
            tickfont=dict(size=18),
            tickvals=list(range(len(data))), 
            ticktext=data['group_name'], 
            showline=True, 
            linecolor='lightgrey', 
            linewidth=1, 
            showgrid=False, 
            zeroline=False
        ),
        height=400,
        showlegend=False,
        template='plotly_white',
    )

    return fig